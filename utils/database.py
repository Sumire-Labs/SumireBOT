"""
SQLiteデータベース管理
"""
from __future__ import annotations

import aiosqlite
import json
from pathlib import Path
from typing import Any, Optional
from datetime import datetime


class Database:
    """非同期SQLiteデータベース管理クラス"""

    _instance: Optional[Database] = None
    _db: Optional[aiosqlite.Connection] = None

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
        """)
        await self._db.commit()

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
