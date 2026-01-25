"""
レベリングシステム関連のデータベース操作
XP、レベル、VC時間、リアクション統計を含む
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import aiosqlite


class LevelingMixin:
    """レベリングシステム関連のデータベース操作"""

    _db: aiosqlite.Connection

    # ==================== レベル設定 ====================

    async def get_leveling_settings(self, guild_id: int) -> Optional[dict]:
        """レベルシステム設定を取得"""
        async with self._db.execute(
            "SELECT * FROM leveling_settings WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                result = dict(row)
                result["ignored_channels"] = json.loads(result.get("ignored_channels", "[]"))
                return result
            return None

    async def set_leveling_enabled(self, guild_id: int, enabled: bool) -> None:
        """レベルシステムの有効/無効を設定"""
        await self._db.execute("""
            INSERT INTO leveling_settings (guild_id, enabled)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                enabled = excluded.enabled
        """, (guild_id, 1 if enabled else 0))
        await self._commit()

    async def add_ignored_channel(self, guild_id: int, channel_id: int) -> None:
        """レベルシステムの除外チャンネルを追加"""
        settings = await self.get_leveling_settings(guild_id)
        ignored = settings.get("ignored_channels", []) if settings else []

        if channel_id not in ignored:
            ignored.append(channel_id)
            await self._db.execute("""
                INSERT INTO leveling_settings (guild_id, ignored_channels)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    ignored_channels = excluded.ignored_channels
            """, (guild_id, json.dumps(ignored)))
            await self._commit()

    async def remove_ignored_channel(self, guild_id: int, channel_id: int) -> None:
        """レベルシステムの除外チャンネルを削除"""
        settings = await self.get_leveling_settings(guild_id)
        if not settings:
            return

        ignored = settings.get("ignored_channels", [])
        if channel_id in ignored:
            ignored.remove(channel_id)
            await self._db.execute(
                "UPDATE leveling_settings SET ignored_channels = ? WHERE guild_id = ?",
                (json.dumps(ignored), guild_id)
            )
            await self._commit()

    # ==================== ユーザーレベル ====================

    async def get_user_level(self, guild_id: int, user_id: int) -> Optional[dict]:
        """ユーザーのレベルデータを取得"""
        async with self._db.execute(
            "SELECT * FROM user_levels WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def get_user_level_with_ranks(self, guild_id: int, user_id: int) -> Optional[dict]:
        """
        ユーザーのレベルデータとランキングを一括取得（N+1クエリ対策）

        Returns:
            dict: ユーザーデータ + text_rank + vc_rank
        """
        async with self._db.execute("""
            SELECT
                u.*,
                (
                    SELECT COUNT(*) + 1 FROM user_levels
                    WHERE guild_id = ? AND (
                        level > u.level OR
                        (level = u.level AND xp > u.xp)
                    )
                ) as text_rank,
                (
                    SELECT COUNT(*) + 1 FROM user_levels
                    WHERE guild_id = ? AND vc_time > COALESCE(u.vc_time, 0)
                ) as vc_rank
            FROM user_levels u
            WHERE u.guild_id = ? AND u.user_id = ?
        """, (guild_id, guild_id, guild_id, user_id)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def add_user_xp(self, guild_id: int, user_id: int, xp_amount: int) -> tuple[int, int, bool]:
        """
        ユーザーにXPを追加し、レベルアップを処理

        Returns:
            tuple[int, int, bool]: (新しいXP, 新しいレベル, レベルアップしたか)
        """
        current = await self.get_user_level(guild_id, user_id)

        if current:
            new_xp = current["xp"] + xp_amount
            old_level = current["level"]
        else:
            new_xp = xp_amount
            old_level = 0

        # レベル計算: 必要XP = レベル × 100
        new_level = old_level
        while new_xp >= (new_level + 1) * 100:
            new_xp -= (new_level + 1) * 100
            new_level += 1

        leveled_up = new_level > old_level

        await self._db.execute("""
            INSERT INTO user_levels (guild_id, user_id, xp, level, last_xp_time)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                xp = excluded.xp,
                level = excluded.level,
                last_xp_time = excluded.last_xp_time
        """, (guild_id, user_id, new_xp, new_level))
        await self._commit()

        return new_xp, new_level, leveled_up

    async def get_user_last_xp_time(self, guild_id: int, user_id: int) -> Optional[datetime]:
        """ユーザーの最終XP獲得時間を取得"""
        async with self._db.execute(
            "SELECT last_xp_time FROM user_levels WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            if row and row["last_xp_time"]:
                return datetime.fromisoformat(row["last_xp_time"])
            return None

    async def get_leaderboard(self, guild_id: int, limit: int = 10) -> list[dict]:
        """サーバーのレベルランキングを取得"""
        async with self._db.execute("""
            SELECT user_id, xp, level FROM user_levels
            WHERE guild_id = ?
            ORDER BY level DESC, xp DESC
            LIMIT ?
        """, (guild_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_user_rank(self, guild_id: int, user_id: int) -> Optional[int]:
        """ユーザーのテキストランキング順位を取得"""
        async with self._db.execute("""
            SELECT COUNT(*) + 1 as rank FROM user_levels
            WHERE guild_id = ? AND (
                level > (SELECT level FROM user_levels WHERE guild_id = ? AND user_id = ?) OR
                (level = (SELECT level FROM user_levels WHERE guild_id = ? AND user_id = ?) AND
                 xp > (SELECT xp FROM user_levels WHERE guild_id = ? AND user_id = ?))
            )
        """, (guild_id, guild_id, user_id, guild_id, user_id, guild_id, user_id)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row["rank"]
            return None

    # ==================== VC時間トラッキング ====================

    async def set_vc_join_time(self, guild_id: int, user_id: int) -> None:
        """VC参加時間を記録"""
        await self._db.execute("""
            INSERT INTO user_levels (guild_id, user_id, vc_join_time)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                vc_join_time = CURRENT_TIMESTAMP
        """, (guild_id, user_id))
        await self._commit()

    async def add_vc_time(self, guild_id: int, user_id: int) -> tuple[int, int, bool]:
        """
        VC退出時に時間を加算し、VCレベルを計算

        Returns:
            tuple[int, int, bool]: (合計VC時間(秒), VCレベル, レベルアップしたか)
        """
        current = await self.get_user_level(guild_id, user_id)

        if not current or not current.get("vc_join_time"):
            return 0, 0, False

        # 参加時間を計算
        join_time = datetime.fromisoformat(current["vc_join_time"])
        time_spent = int((datetime.utcnow() - join_time).total_seconds())

        if time_spent < 0:
            time_spent = 0

        new_vc_time = current.get("vc_time", 0) + time_spent
        old_vc_level = current.get("vc_level", 0)

        # VCレベル計算: 1時間(3600秒) = 1レベル
        new_vc_level = new_vc_time // 3600

        leveled_up = new_vc_level > old_vc_level

        await self._db.execute("""
            UPDATE user_levels
            SET vc_time = ?, vc_level = ?, vc_join_time = NULL
            WHERE guild_id = ? AND user_id = ?
        """, (new_vc_time, new_vc_level, guild_id, user_id))
        await self._commit()

        return new_vc_time, new_vc_level, leveled_up

    async def clear_vc_join_time(self, guild_id: int, user_id: int) -> None:
        """VC参加時間をクリア（異常終了時用）"""
        await self._db.execute("""
            UPDATE user_levels SET vc_join_time = NULL
            WHERE guild_id = ? AND user_id = ?
        """, (guild_id, user_id))
        await self._commit()

    async def get_vc_leaderboard(self, guild_id: int, limit: int = 10) -> list[dict]:
        """サーバーのVC時間ランキングを取得"""
        async with self._db.execute("""
            SELECT user_id, vc_time, vc_level FROM user_levels
            WHERE guild_id = ? AND vc_time > 0
            ORDER BY vc_time DESC
            LIMIT ?
        """, (guild_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_user_vc_rank(self, guild_id: int, user_id: int) -> Optional[int]:
        """ユーザーのVCランキング順位を取得"""
        async with self._db.execute("""
            SELECT COUNT(*) + 1 as rank FROM user_levels
            WHERE guild_id = ? AND vc_time > (
                SELECT COALESCE(vc_time, 0) FROM user_levels WHERE guild_id = ? AND user_id = ?
            )
        """, (guild_id, guild_id, user_id)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row["rank"]
            return None

    # ==================== リアクション統計 ====================

    async def add_reaction_given(self, guild_id: int, user_id: int) -> None:
        """リアクションをつけた数をインクリメント"""
        await self._db.execute("""
            INSERT INTO user_levels (guild_id, user_id, reactions_given)
            VALUES (?, ?, 1)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                reactions_given = reactions_given + 1
        """, (guild_id, user_id))
        await self._commit()

    async def add_reaction_received(self, guild_id: int, user_id: int) -> None:
        """リアクションをもらった数をインクリメント"""
        await self._db.execute("""
            INSERT INTO user_levels (guild_id, user_id, reactions_received)
            VALUES (?, ?, 1)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                reactions_received = reactions_received + 1
        """, (guild_id, user_id))
        await self._commit()

    # ==================== Web API用メソッド ====================

    async def set_leveling_ignored_channels(self, guild_id: int, channel_ids: list[int]) -> None:
        """レベリングの除外チャンネルを一括設定"""
        await self._db.execute("""
            INSERT INTO leveling_settings (guild_id, ignored_channels)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                ignored_channels = excluded.ignored_channels
        """, (guild_id, json.dumps(channel_ids)))
        await self._commit()

    async def get_level_leaderboard(self, guild_id: int, limit: int = 50, offset: int = 0) -> list[dict]:
        """レベルランキングを取得（ページネーション対応）"""
        async with self._db.execute("""
            SELECT user_id, xp, level FROM user_levels
            WHERE guild_id = ?
            ORDER BY level DESC, xp DESC
            LIMIT ? OFFSET ?
        """, (guild_id, limit, offset)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_level_user_count(self, guild_id: int) -> int:
        """レベルデータを持つユーザー数を取得"""
        async with self._db.execute(
            "SELECT COUNT(*) as count FROM user_levels WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row["count"] if row else 0

    async def get_reaction_given_leaderboard(self, guild_id: int, limit: int = 50) -> list[dict]:
        """リアクションを与えた数ランキング"""
        async with self._db.execute("""
            SELECT user_id, reactions_given, reactions_received FROM user_levels
            WHERE guild_id = ? AND reactions_given > 0
            ORDER BY reactions_given DESC
            LIMIT ?
        """, (guild_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_reaction_received_leaderboard(self, guild_id: int, limit: int = 50) -> list[dict]:
        """リアクションを受けた数ランキング"""
        async with self._db.execute("""
            SELECT user_id, reactions_given, reactions_received FROM user_levels
            WHERE guild_id = ? AND reactions_received > 0
            ORDER BY reactions_received DESC
            LIMIT ?
        """, (guild_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
