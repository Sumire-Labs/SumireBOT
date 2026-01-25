"""
スター評価関連のデータベース操作
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import aiosqlite


class StarMixin:
    """スター評価関連のデータベース操作"""

    _db: aiosqlite.Connection

    # ==================== スター設定 ====================

    async def get_star_settings(self, guild_id: int) -> Optional[dict]:
        """スター設定を取得"""
        async with self._db.execute(
            "SELECT * FROM star_settings WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                result = dict(row)
                result["target_channels"] = json.loads(result.get("target_channels", "[]"))
                return result
            return None

    async def set_star_enabled(self, guild_id: int, enabled: bool) -> None:
        """スター機能の有効/無効を設定"""
        await self._db.execute("""
            INSERT INTO star_settings (guild_id, enabled)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                enabled = excluded.enabled
        """, (guild_id, 1 if enabled else 0))
        await self._commit()

    async def add_star_channel(self, guild_id: int, channel_id: int) -> None:
        """スター対象チャンネルを追加"""
        settings = await self.get_star_settings(guild_id)
        channels = settings.get("target_channels", []) if settings else []

        if channel_id not in channels:
            channels.append(channel_id)
            await self._db.execute("""
                INSERT INTO star_settings (guild_id, target_channels)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    target_channels = excluded.target_channels
            """, (guild_id, json.dumps(channels)))
            await self._commit()

    async def remove_star_channel(self, guild_id: int, channel_id: int) -> None:
        """スター対象チャンネルを削除"""
        settings = await self.get_star_settings(guild_id)
        if not settings:
            return

        channels = settings.get("target_channels", [])
        if channel_id in channels:
            channels.remove(channel_id)
            await self._db.execute(
                "UPDATE star_settings SET target_channels = ? WHERE guild_id = ?",
                (json.dumps(channels), guild_id)
            )
            await self._commit()

    async def clear_star_channels(self, guild_id: int) -> None:
        """スター対象チャンネルをすべてクリア"""
        await self._db.execute(
            "UPDATE star_settings SET target_channels = '[]' WHERE guild_id = ?",
            (guild_id,)
        )
        await self._commit()

    async def set_weekly_report_channel(self, guild_id: int, channel_id: Optional[int]) -> None:
        """週間レポート送信チャンネルを設定"""
        await self._db.execute("""
            INSERT INTO star_settings (guild_id, weekly_report_channel_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                weekly_report_channel_id = excluded.weekly_report_channel_id
        """, (guild_id, channel_id))
        await self._commit()

    async def update_weekly_report_last_sent(self, guild_id: int) -> None:
        """週間レポート最終送信日時を更新"""
        await self._db.execute("""
            UPDATE star_settings SET weekly_report_last_sent = CURRENT_TIMESTAMP
            WHERE guild_id = ?
        """, (guild_id,))
        await self._commit()

    async def get_guilds_for_weekly_report(self) -> list[dict]:
        """週間レポートを送信すべきサーバー一覧を取得"""
        async with self._db.execute("""
            SELECT guild_id, weekly_report_channel_id, weekly_report_last_sent
            FROM star_settings
            WHERE enabled = 1
              AND weekly_report_channel_id IS NOT NULL
        """) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ==================== スターメッセージ ====================

    async def create_star_message(
        self,
        guild_id: int,
        channel_id: int,
        message_id: int,
        author_id: int
    ) -> int:
        """スターメッセージを作成"""
        cursor = await self._db.execute("""
            INSERT INTO star_messages (guild_id, channel_id, message_id, author_id)
            VALUES (?, ?, ?, ?)
        """, (guild_id, channel_id, message_id, author_id))
        await self._commit()
        return cursor.lastrowid

    async def get_star_message(self, message_id: int) -> Optional[dict]:
        """スターメッセージを取得"""
        async with self._db.execute(
            "SELECT * FROM star_messages WHERE message_id = ?",
            (message_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                result = dict(row)
                result["starred_users"] = json.loads(result.get("starred_users", "[]"))
                return result
            return None

    async def add_star(self, message_id: int, user_id: int) -> bool:
        """
        スターを追加（重複チェック付き）

        Returns:
            bool: スターが追加された場合True、既にスター済みの場合False
        """
        star_msg = await self.get_star_message(message_id)
        if not star_msg:
            return False

        starred_users = star_msg["starred_users"]
        if user_id in starred_users:
            return False

        starred_users.append(user_id)
        new_count = len(starred_users)

        await self._db.execute(
            "UPDATE star_messages SET starred_users = ?, star_count = ? WHERE message_id = ?",
            (json.dumps(starred_users), new_count, message_id)
        )
        await self._commit()
        return True

    async def remove_star(self, message_id: int, user_id: int) -> bool:
        """
        スターを削除

        Returns:
            bool: スターが削除された場合True、存在しなかった場合False
        """
        star_msg = await self.get_star_message(message_id)
        if not star_msg:
            return False

        starred_users = star_msg["starred_users"]
        if user_id not in starred_users:
            return False

        starred_users.remove(user_id)
        new_count = len(starred_users)

        await self._db.execute(
            "UPDATE star_messages SET starred_users = ?, star_count = ? WHERE message_id = ?",
            (json.dumps(starred_users), new_count, message_id)
        )
        await self._commit()
        return True

    async def get_star_leaderboard(
        self,
        guild_id: int,
        limit: int = 10,
        since: Optional[datetime] = None
    ) -> list[dict]:
        """
        スターランキングを取得（時間フィルター対応）

        Args:
            guild_id: サーバーID
            limit: 取得件数
            since: この日時以降のメッセージのみ対象（Noneの場合は全期間）
        """
        if since:
            query = """
                SELECT message_id, channel_id, author_id, star_count, created_at
                FROM star_messages
                WHERE guild_id = ? AND created_at >= ? AND star_count > 0
                ORDER BY star_count DESC, created_at DESC
                LIMIT ?
            """
            params = (guild_id, since.isoformat(), limit)
        else:
            query = """
                SELECT message_id, channel_id, author_id, star_count, created_at
                FROM star_messages
                WHERE guild_id = ? AND star_count > 0
                ORDER BY star_count DESC, created_at DESC
                LIMIT ?
            """
            params = (guild_id, limit)

        async with self._db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_author_star_totals(
        self,
        guild_id: int,
        limit: int = 10,
        since: Optional[datetime] = None
    ) -> list[dict]:
        """
        投稿者別スター合計ランキング

        Args:
            guild_id: サーバーID
            limit: 取得件数
            since: この日時以降のメッセージのみ対象
        """
        if since:
            query = """
                SELECT author_id, SUM(star_count) as total_stars, COUNT(*) as post_count
                FROM star_messages
                WHERE guild_id = ? AND created_at >= ?
                GROUP BY author_id
                HAVING total_stars > 0
                ORDER BY total_stars DESC
                LIMIT ?
            """
            params = (guild_id, since.isoformat(), limit)
        else:
            query = """
                SELECT author_id, SUM(star_count) as total_stars, COUNT(*) as post_count
                FROM star_messages
                WHERE guild_id = ?
                GROUP BY author_id
                HAVING total_stars > 0
                ORDER BY total_stars DESC
                LIMIT ?
            """
            params = (guild_id, limit)

        async with self._db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def delete_star_message(self, message_id: int) -> None:
        """スターメッセージを削除"""
        await self._db.execute(
            "DELETE FROM star_messages WHERE message_id = ?",
            (message_id,)
        )
        await self._commit()

    # ==================== Web API用メソッド ====================

    async def set_star_target_channels(self, guild_id: int, channel_ids: list[int]) -> None:
        """スター対象チャンネルを一括設定"""
        await self._db.execute("""
            INSERT INTO star_settings (guild_id, target_channels)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                target_channels = excluded.target_channels
        """, (guild_id, json.dumps(channel_ids)))
        await self._commit()

    async def set_star_weekly_report_channel(self, guild_id: int, channel_id: Optional[int]) -> None:
        """週間レポートチャンネルを設定（set_weekly_report_channelのエイリアス）"""
        await self.set_weekly_report_channel(guild_id, channel_id)

    async def get_star_user_leaderboard(self, guild_id: int, limit: int = 50) -> list[dict]:
        """ユーザー別スターランキング"""
        async with self._db.execute("""
            SELECT author_id, SUM(star_count) as total_stars, COUNT(*) as message_count
            FROM star_messages
            WHERE guild_id = ?
            GROUP BY author_id
            HAVING total_stars > 0
            ORDER BY total_stars DESC
            LIMIT ?
        """, (guild_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_star_message_leaderboard(self, guild_id: int, limit: int = 50) -> list[dict]:
        """メッセージ別スターランキング"""
        async with self._db.execute("""
            SELECT message_id, channel_id, author_id, star_count
            FROM star_messages
            WHERE guild_id = ? AND star_count > 0
            ORDER BY star_count DESC
            LIMIT ?
        """, (guild_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_star_message_count(self, guild_id: int) -> int:
        """スター付きメッセージの総数"""
        async with self._db.execute(
            "SELECT COUNT(*) as count FROM star_messages WHERE guild_id = ? AND star_count > 0",
            (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row["count"] if row else 0
