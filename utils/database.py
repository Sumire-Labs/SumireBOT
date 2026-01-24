"""
SQLiteデータベース管理
"""
from __future__ import annotations

import aiosqlite
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional, AsyncIterator
from datetime import datetime


class Database:
    """非同期SQLiteデータベース管理クラス"""

    _instance: Optional[Database] = None
    _db: Optional[aiosqlite.Connection] = None
    _in_transaction: bool = False

    def __new__(cls) -> Database:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self, db_path: str) -> None:
        """データベースに接続"""
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        self._db = await aiosqlite.connect(db_path)
        self._db.row_factory = aiosqlite.Row

        # WALモード有効化（読み書き並列可能、ロック競合軽減）
        await self._db.execute("PRAGMA journal_mode=WAL")

        await self._init_tables()

    async def close(self) -> None:
        """データベース接続を閉じる"""
        if self._db:
            await self._db.close()
            self._db = None

    async def _init_tables(self) -> None:
        """テーブルを初期化"""
        await self._db.executescript("""
            -- サーバー設定
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'ja',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- ログ設定（サーバーごと）
            CREATE TABLE IF NOT EXISTS logger_settings (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                enabled INTEGER DEFAULT 0,
                log_messages INTEGER DEFAULT 1,
                log_channels INTEGER DEFAULT 1,
                log_roles INTEGER DEFAULT 1,
                log_members INTEGER DEFAULT 1
            );

            -- チケット設定（サーバーごと）
            CREATE TABLE IF NOT EXISTS ticket_settings (
                guild_id INTEGER PRIMARY KEY,
                category_id INTEGER,
                panel_channel_id INTEGER,
                panel_message_id INTEGER,
                ticket_counter INTEGER DEFAULT 0
            );

            -- アクティブチケット
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                ticket_number INTEGER NOT NULL,
                category TEXT,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP
            );

            -- 永続的View管理
            CREATE TABLE IF NOT EXISTS persistent_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                view_type TEXT NOT NULL,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(message_id)
            );

            -- 音楽設定（サーバーごと）
            CREATE TABLE IF NOT EXISTS music_settings (
                guild_id INTEGER PRIMARY KEY,
                default_volume INTEGER DEFAULT 50,
                dj_role_id INTEGER,
                music_channel_id INTEGER
            );

            -- 自動ロール設定（サーバーごと）
            CREATE TABLE IF NOT EXISTS autorole_settings (
                guild_id INTEGER PRIMARY KEY,
                human_role_id INTEGER,
                bot_role_id INTEGER,
                enabled INTEGER DEFAULT 1
            );

            -- レベルシステム設定（サーバーごと）
            CREATE TABLE IF NOT EXISTS leveling_settings (
                guild_id INTEGER PRIMARY KEY,
                enabled INTEGER DEFAULT 1,
                ignored_channels TEXT DEFAULT '[]'
            );

            -- ユーザーレベルデータ
            CREATE TABLE IF NOT EXISTS user_levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                last_xp_time TIMESTAMP,
                vc_time INTEGER DEFAULT 0,
                vc_level INTEGER DEFAULT 0,
                vc_join_time TIMESTAMP,
                reactions_given INTEGER DEFAULT 0,
                reactions_received INTEGER DEFAULT 0,
                UNIQUE(guild_id, user_id)
            );

            -- Giveaway
            CREATE TABLE IF NOT EXISTS giveaways (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER UNIQUE NOT NULL,
                host_id INTEGER NOT NULL,
                prize TEXT NOT NULL,
                winner_count INTEGER DEFAULT 1,
                end_time TIMESTAMP NOT NULL,
                participants TEXT DEFAULT '[]',
                winners TEXT DEFAULT '[]',
                ended INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 投票
            CREATE TABLE IF NOT EXISTS polls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER UNIQUE NOT NULL,
                author_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                options TEXT NOT NULL,
                votes TEXT DEFAULT '{}',
                multi_select INTEGER DEFAULT 0,
                end_time TIMESTAMP,
                ended INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- スター設定（サーバーごと）
            CREATE TABLE IF NOT EXISTS star_settings (
                guild_id INTEGER PRIMARY KEY,
                enabled INTEGER DEFAULT 1,
                target_channels TEXT DEFAULT '[]'
            );

            -- スターメッセージトラッキング
            CREATE TABLE IF NOT EXISTS star_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER UNIQUE NOT NULL,
                author_id INTEGER NOT NULL,
                star_count INTEGER DEFAULT 0,
                starred_users TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- チーム分けくじパネル
            CREATE TABLE IF NOT EXISTS team_shuffle_panels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER UNIQUE NOT NULL,
                creator_id INTEGER NOT NULL,
                title TEXT DEFAULT 'チーム分けくじ',
                team_count INTEGER DEFAULT 2,
                participants TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- パフォーマンス向上用インデックス
            CREATE INDEX IF NOT EXISTS idx_user_levels_guild_user ON user_levels(guild_id, user_id);
            CREATE INDEX IF NOT EXISTS idx_user_levels_ranking ON user_levels(guild_id, level DESC, xp DESC);
            CREATE INDEX IF NOT EXISTS idx_tickets_guild_user ON tickets(guild_id, user_id, status);
            CREATE INDEX IF NOT EXISTS idx_giveaways_active ON giveaways(ended, end_time);
            CREATE INDEX IF NOT EXISTS idx_polls_active ON polls(ended, end_time);
            CREATE INDEX IF NOT EXISTS idx_star_messages_guild ON star_messages(guild_id, star_count DESC);
        """)
        await self._db.commit()

        # 既存テーブルにカラムを追加（マイグレーション）
        await self._migrate_user_levels_reactions()

    async def _migrate_user_levels_reactions(self) -> None:
        """user_levelsテーブルにリアクションカラムを追加（既存DB用マイグレーション）"""
        # ALTER TABLEはカラムが既に存在するとエラーになるので、各カラムを個別にtry-except
        try:
            await self._db.execute(
                "ALTER TABLE user_levels ADD COLUMN reactions_given INTEGER DEFAULT 0"
            )
            await self._db.commit()
        except Exception:
            pass

        try:
            await self._db.execute(
                "ALTER TABLE user_levels ADD COLUMN reactions_received INTEGER DEFAULT 0"
            )
            await self._db.commit()
        except Exception:
            pass

    # ==================== サーバー設定 ====================

    async def ensure_guild(self, guild_id: int) -> None:
        """サーバー設定が存在することを保証"""
        await self._db.execute(
            "INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)",
            (guild_id,)
        )
        await self._db.commit()

    async def get_guild_language(self, guild_id: int) -> str:
        """サーバーの言語設定を取得"""
        await self.ensure_guild(guild_id)
        async with self._db.execute(
            "SELECT language FROM guild_settings WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row["language"] if row else "ja"

    # ==================== ログ設定 ====================

    async def get_logger_settings(self, guild_id: int) -> Optional[dict]:
        """ログ設定を取得"""
        async with self._db.execute(
            "SELECT * FROM logger_settings WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def set_logger_channel(self, guild_id: int, channel_id: int) -> None:
        """ログチャンネルを設定"""
        await self._db.execute("""
            INSERT INTO logger_settings (guild_id, channel_id, enabled)
            VALUES (?, ?, 1)
            ON CONFLICT(guild_id) DO UPDATE SET
                channel_id = excluded.channel_id,
                enabled = 1
        """, (guild_id, channel_id))
        await self._db.commit()

    async def disable_logger(self, guild_id: int) -> None:
        """ログを無効化"""
        await self._db.execute(
            "UPDATE logger_settings SET enabled = 0 WHERE guild_id = ?",
            (guild_id,)
        )
        await self._db.commit()

    async def update_logger_settings(
        self,
        guild_id: int,
        log_messages: Optional[bool] = None,
        log_channels: Optional[bool] = None,
        log_roles: Optional[bool] = None,
        log_members: Optional[bool] = None
    ) -> None:
        """ログ設定を更新"""
        updates = []
        params = []

        if log_messages is not None:
            updates.append("log_messages = ?")
            params.append(int(log_messages))
        if log_channels is not None:
            updates.append("log_channels = ?")
            params.append(int(log_channels))
        if log_roles is not None:
            updates.append("log_roles = ?")
            params.append(int(log_roles))
        if log_members is not None:
            updates.append("log_members = ?")
            params.append(int(log_members))

        if updates:
            params.append(guild_id)
            await self._db.execute(
                f"UPDATE logger_settings SET {', '.join(updates)} WHERE guild_id = ?",
                params
            )
            await self._db.commit()

    # ==================== チケット設定 ====================

    async def get_ticket_settings(self, guild_id: int) -> Optional[dict]:
        """チケット設定を取得"""
        async with self._db.execute(
            "SELECT * FROM ticket_settings WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def setup_ticket_system(
        self,
        guild_id: int,
        category_id: int,
        panel_channel_id: int,
        panel_message_id: int
    ) -> None:
        """チケットシステムをセットアップ"""
        await self._db.execute("""
            INSERT INTO ticket_settings (guild_id, category_id, panel_channel_id, panel_message_id, ticket_counter)
            VALUES (?, ?, ?, ?, 0)
            ON CONFLICT(guild_id) DO UPDATE SET
                category_id = excluded.category_id,
                panel_channel_id = excluded.panel_channel_id,
                panel_message_id = excluded.panel_message_id
        """, (guild_id, category_id, panel_channel_id, panel_message_id))
        await self._db.commit()

    async def get_next_ticket_number(self, guild_id: int) -> int:
        """次のチケット番号を取得して更新"""
        async with self._db.execute(
            "SELECT ticket_counter FROM ticket_settings WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            next_number = (row["ticket_counter"] if row else 0) + 1

        await self._db.execute(
            "UPDATE ticket_settings SET ticket_counter = ? WHERE guild_id = ?",
            (next_number, guild_id)
        )
        await self._db.commit()
        return next_number

    # ==================== チケット管理 ====================

    async def create_ticket(
        self,
        guild_id: int,
        channel_id: int,
        user_id: int,
        ticket_number: int
    ) -> int:
        """チケットを作成"""
        cursor = await self._db.execute("""
            INSERT INTO tickets (guild_id, channel_id, user_id, ticket_number)
            VALUES (?, ?, ?, ?)
        """, (guild_id, channel_id, user_id, ticket_number))
        await self._db.commit()
        return cursor.lastrowid

    async def get_ticket_by_channel(self, channel_id: int) -> Optional[dict]:
        """チャンネルIDからチケットを取得"""
        async with self._db.execute(
            "SELECT * FROM tickets WHERE channel_id = ?",
            (channel_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def update_ticket_status(self, channel_id: int, status: str) -> None:
        """チケットのステータスを更新"""
        closed_at = datetime.utcnow().isoformat() if status == "closed" else None
        await self._db.execute(
            "UPDATE tickets SET status = ?, closed_at = ? WHERE channel_id = ?",
            (status, closed_at, channel_id)
        )
        await self._db.commit()

    async def update_ticket_category(self, channel_id: int, category: str) -> None:
        """チケットのカテゴリを更新"""
        await self._db.execute(
            "UPDATE tickets SET category = ? WHERE channel_id = ?",
            (category, channel_id)
        )
        await self._db.commit()

    async def get_user_open_tickets(self, guild_id: int, user_id: int) -> list[dict]:
        """ユーザーのオープンなチケットを取得"""
        async with self._db.execute(
            "SELECT * FROM tickets WHERE guild_id = ? AND user_id = ? AND status != 'closed'",
            (guild_id, user_id)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ==================== 永続的View管理 ====================

    async def save_persistent_view(
        self,
        guild_id: int,
        channel_id: int,
        message_id: int,
        view_type: str,
        data: Optional[dict] = None
    ) -> None:
        """永続的Viewを保存"""
        data_json = json.dumps(data) if data else None
        await self._db.execute("""
            INSERT INTO persistent_views (guild_id, channel_id, message_id, view_type, data)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(message_id) DO UPDATE SET
                view_type = excluded.view_type,
                data = excluded.data
        """, (guild_id, channel_id, message_id, view_type, data_json))
        await self._db.commit()

    async def get_persistent_views(self, view_type: Optional[str] = None) -> list[dict]:
        """永続的Viewを取得"""
        if view_type:
            query = "SELECT * FROM persistent_views WHERE view_type = ?"
            params = (view_type,)
        else:
            query = "SELECT * FROM persistent_views"
            params = ()

        async with self._db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                if d.get("data"):
                    d["data"] = json.loads(d["data"])
                result.append(d)
            return result

    async def delete_persistent_view(self, message_id: int) -> None:
        """永続的Viewを削除"""
        await self._db.execute(
            "DELETE FROM persistent_views WHERE message_id = ?",
            (message_id,)
        )
        await self._db.commit()

    # ==================== 音楽設定 ====================

    async def get_music_settings(self, guild_id: int) -> Optional[dict]:
        """音楽設定を取得"""
        async with self._db.execute(
            "SELECT * FROM music_settings WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def set_music_volume(self, guild_id: int, volume: int) -> None:
        """音楽のデフォルト音量を設定"""
        await self._db.execute("""
            INSERT INTO music_settings (guild_id, default_volume)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                default_volume = excluded.default_volume
        """, (guild_id, volume))
        await self._db.commit()

    # ==================== 自動ロール設定 ====================

    async def get_autorole_settings(self, guild_id: int) -> Optional[dict]:
        """自動ロール設定を取得"""
        async with self._db.execute(
            "SELECT * FROM autorole_settings WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def set_autorole(
        self,
        guild_id: int,
        human_role_id: Optional[int] = None,
        bot_role_id: Optional[int] = None,
        enabled: Optional[bool] = None
    ) -> None:
        """自動ロール設定を保存"""
        # 既存の設定を取得
        current = await self.get_autorole_settings(guild_id)

        if current:
            # 更新
            new_human = human_role_id if human_role_id is not None else current.get("human_role_id")
            new_bot = bot_role_id if bot_role_id is not None else current.get("bot_role_id")
            new_enabled = (1 if enabled else 0) if enabled is not None else current.get("enabled", 1)

            await self._db.execute("""
                UPDATE autorole_settings
                SET human_role_id = ?, bot_role_id = ?, enabled = ?
                WHERE guild_id = ?
            """, (new_human, new_bot, new_enabled, guild_id))
        else:
            # 新規作成
            await self._db.execute("""
                INSERT INTO autorole_settings (guild_id, human_role_id, bot_role_id, enabled)
                VALUES (?, ?, ?, ?)
            """, (guild_id, human_role_id, bot_role_id, 1 if enabled is None else (1 if enabled else 0)))

        await self._db.commit()

    async def clear_autorole(self, guild_id: int, role_type: str) -> None:
        """自動ロール設定をクリア（human または bot）"""
        if role_type == "human":
            await self._db.execute(
                "UPDATE autorole_settings SET human_role_id = NULL WHERE guild_id = ?",
                (guild_id,)
            )
        elif role_type == "bot":
            await self._db.execute(
                "UPDATE autorole_settings SET bot_role_id = NULL WHERE guild_id = ?",
                (guild_id,)
            )
        await self._db.commit()

    # ==================== レベルシステム ====================

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
        await self._db.commit()

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
            await self._db.commit()

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
            await self._db.commit()

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
        await self._db.commit()

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
        await self._db.commit()

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
        await self._db.commit()

        return new_vc_time, new_vc_level, leveled_up

    async def clear_vc_join_time(self, guild_id: int, user_id: int) -> None:
        """VC参加時間をクリア（異常終了時用）"""
        await self._db.execute("""
            UPDATE user_levels SET vc_join_time = NULL
            WHERE guild_id = ? AND user_id = ?
        """, (guild_id, user_id))
        await self._db.commit()

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
        await self._db.commit()

    async def add_reaction_received(self, guild_id: int, user_id: int) -> None:
        """リアクションをもらった数をインクリメント"""
        await self._db.execute("""
            INSERT INTO user_levels (guild_id, user_id, reactions_received)
            VALUES (?, ?, 1)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                reactions_received = reactions_received + 1
        """, (guild_id, user_id))
        await self._db.commit()

    # ==================== Giveaway ====================

    async def create_giveaway(
        self,
        guild_id: int,
        channel_id: int,
        message_id: int,
        host_id: int,
        prize: str,
        winner_count: int,
        end_time: datetime
    ) -> int:
        """Giveawayを作成"""
        cursor = await self._db.execute("""
            INSERT INTO giveaways (guild_id, channel_id, message_id, host_id, prize, winner_count, end_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (guild_id, channel_id, message_id, host_id, prize, winner_count, end_time.isoformat()))
        await self._db.commit()
        return cursor.lastrowid

    async def get_giveaway(self, message_id: int) -> Optional[dict]:
        """Giveawayを取得"""
        async with self._db.execute(
            "SELECT * FROM giveaways WHERE message_id = ?",
            (message_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                result = dict(row)
                result["participants"] = json.loads(result.get("participants", "[]"))
                result["winners"] = json.loads(result.get("winners", "[]"))
                return result
            return None

    async def get_active_giveaways(self) -> list[dict]:
        """終了していないGiveawayを全て取得"""
        async with self._db.execute(
            "SELECT * FROM giveaways WHERE ended = 0"
        ) as cursor:
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                result = dict(row)
                result["participants"] = json.loads(result.get("participants", "[]"))
                result["winners"] = json.loads(result.get("winners", "[]"))
                results.append(result)
            return results

    async def add_giveaway_participant(self, message_id: int, user_id: int) -> bool:
        """Giveawayに参加者を追加（既に参加済みの場合はFalse）"""
        giveaway = await self.get_giveaway(message_id)
        if not giveaway:
            return False

        participants = giveaway["participants"]
        if user_id in participants:
            return False

        participants.append(user_id)
        await self._db.execute(
            "UPDATE giveaways SET participants = ? WHERE message_id = ?",
            (json.dumps(participants), message_id)
        )
        await self._db.commit()
        return True

    async def end_giveaway(self, message_id: int, winners: list[int]) -> None:
        """Giveawayを終了"""
        await self._db.execute(
            "UPDATE giveaways SET ended = 1, winners = ? WHERE message_id = ?",
            (json.dumps(winners), message_id)
        )
        await self._db.commit()

    async def delete_giveaway(self, message_id: int) -> None:
        """Giveawayを削除"""
        await self._db.execute(
            "DELETE FROM giveaways WHERE message_id = ?",
            (message_id,)
        )
        await self._db.commit()

    # ==================== 投票 ====================

    async def create_poll(
        self,
        guild_id: int,
        channel_id: int,
        message_id: int,
        author_id: int,
        question: str,
        options: list[str],
        multi_select: bool = False,
        end_time: Optional[datetime] = None
    ) -> int:
        """投票を作成"""
        cursor = await self._db.execute("""
            INSERT INTO polls (guild_id, channel_id, message_id, author_id, question, options, multi_select, end_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            guild_id, channel_id, message_id, author_id, question,
            json.dumps(options), 1 if multi_select else 0,
            end_time.isoformat() if end_time else None
        ))
        await self._db.commit()
        return cursor.lastrowid

    async def get_poll(self, message_id: int) -> Optional[dict]:
        """投票を取得"""
        async with self._db.execute(
            "SELECT * FROM polls WHERE message_id = ?",
            (message_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                result = dict(row)
                result["options"] = json.loads(result.get("options", "[]"))
                result["votes"] = json.loads(result.get("votes", "{}"))
                return result
            return None

    async def get_active_polls(self) -> list[dict]:
        """終了していない投票を全て取得"""
        async with self._db.execute(
            "SELECT * FROM polls WHERE ended = 0"
        ) as cursor:
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                result = dict(row)
                result["options"] = json.loads(result.get("options", "[]"))
                result["votes"] = json.loads(result.get("votes", "{}"))
                results.append(result)
            return results

    async def vote_poll(self, message_id: int, user_id: int, option_index: int) -> bool:
        """
        投票する

        Returns:
            bool: 投票が変更されたかどうか
        """
        poll = await self.get_poll(message_id)
        if not poll or poll["ended"]:
            return False

        votes = poll["votes"]
        user_key = str(user_id)
        multi_select = bool(poll["multi_select"])

        if multi_select:
            # 複数選択: トグル
            if user_key not in votes:
                votes[user_key] = []
            if option_index in votes[user_key]:
                votes[user_key].remove(option_index)
            else:
                votes[user_key].append(option_index)
        else:
            # 単一選択: 上書き
            votes[user_key] = [option_index]

        await self._db.execute(
            "UPDATE polls SET votes = ? WHERE message_id = ?",
            (json.dumps(votes), message_id)
        )
        await self._db.commit()
        return True

    async def end_poll(self, message_id: int) -> None:
        """投票を終了"""
        await self._db.execute(
            "UPDATE polls SET ended = 1 WHERE message_id = ?",
            (message_id,)
        )
        await self._db.commit()

    async def delete_poll(self, message_id: int) -> None:
        """投票を削除"""
        await self._db.execute(
            "DELETE FROM polls WHERE message_id = ?",
            (message_id,)
        )
        await self._db.commit()

    # ==================== スター評価 ====================

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
        await self._db.commit()

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
            await self._db.commit()

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
            await self._db.commit()

    async def clear_star_channels(self, guild_id: int) -> None:
        """スター対象チャンネルをすべてクリア"""
        await self._db.execute(
            "UPDATE star_settings SET target_channels = '[]' WHERE guild_id = ?",
            (guild_id,)
        )
        await self._db.commit()

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
        await self._db.commit()
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
        await self._db.commit()
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
        await self._db.commit()
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
        await self._db.commit()

    # ==================== チーム分けくじ ====================

    async def create_team_shuffle_panel(
        self,
        guild_id: int,
        channel_id: int,
        message_id: int,
        creator_id: int,
        title: str = "チーム分けくじ"
    ) -> int:
        """チーム分けくじパネルを作成"""
        cursor = await self._db.execute("""
            INSERT INTO team_shuffle_panels (guild_id, channel_id, message_id, creator_id, title)
            VALUES (?, ?, ?, ?, ?)
        """, (guild_id, channel_id, message_id, creator_id, title))
        await self._db.commit()
        return cursor.lastrowid

    async def get_team_shuffle_panel(self, message_id: int) -> Optional[dict]:
        """チーム分けくじパネルを取得"""
        async with self._db.execute(
            "SELECT * FROM team_shuffle_panels WHERE message_id = ?",
            (message_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                result = dict(row)
                result["participants"] = json.loads(result.get("participants", "[]"))
                return result
            return None

    async def add_team_shuffle_participant(self, message_id: int, user_id: int) -> bool:
        """
        チーム分けくじに参加者を追加

        Returns:
            bool: 追加された場合True、既に参加済みの場合False
        """
        panel = await self.get_team_shuffle_panel(message_id)
        if not panel:
            return False

        participants = panel["participants"]
        if user_id in participants:
            return False

        participants.append(user_id)
        await self._db.execute(
            "UPDATE team_shuffle_panels SET participants = ? WHERE message_id = ?",
            (json.dumps(participants), message_id)
        )
        await self._db.commit()
        return True

    async def remove_team_shuffle_participant(self, message_id: int, user_id: int) -> bool:
        """
        チーム分けくじから参加者を削除

        Returns:
            bool: 削除された場合True、参加していなかった場合False
        """
        panel = await self.get_team_shuffle_panel(message_id)
        if not panel:
            return False

        participants = panel["participants"]
        if user_id not in participants:
            return False

        participants.remove(user_id)
        await self._db.execute(
            "UPDATE team_shuffle_panels SET participants = ? WHERE message_id = ?",
            (json.dumps(participants), message_id)
        )
        await self._db.commit()
        return True

    async def update_team_shuffle_team_count(self, message_id: int, team_count: int) -> bool:
        """
        チーム分けくじのチーム数を更新

        Returns:
            bool: 更新された場合True
        """
        panel = await self.get_team_shuffle_panel(message_id)
        if not panel:
            return False

        await self._db.execute(
            "UPDATE team_shuffle_panels SET team_count = ? WHERE message_id = ?",
            (team_count, message_id)
        )
        await self._db.commit()
        return True

    async def delete_team_shuffle_panel(self, message_id: int) -> None:
        """チーム分けくじパネルを削除"""
        await self._db.execute(
            "DELETE FROM team_shuffle_panels WHERE message_id = ?",
            (message_id,)
        )
        await self._db.commit()
