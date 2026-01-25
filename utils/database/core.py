"""
データベースコア機能
接続管理、トランザクション、テーブル初期化を担当
"""
from __future__ import annotations

import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, AsyncIterator


class DatabaseCore:
    """データベース接続とトランザクション管理（シングルトン）"""

    _instance: Optional[DatabaseCore] = None
    _db: Optional[aiosqlite.Connection] = None
    _in_transaction: bool = False

    def __new__(cls) -> DatabaseCore:
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

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        """
        トランザクションコンテキストマネージャー
        複数の操作をまとめてcommitし、I/Oを削減

        Usage:
            async with db.transaction():
                await db.add_user_xp(...)
                await db.add_reaction_given(...)
            # ここで自動commit
        """
        self._in_transaction = True
        try:
            yield
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            raise
        finally:
            self._in_transaction = False

    async def _commit_if_not_in_transaction(self) -> None:
        """トランザクション外の場合のみcommit"""
        if not self._in_transaction:
            await self._db.commit()

    async def _commit(self) -> None:
        """内部用commit（トランザクション対応）"""
        await self._commit_if_not_in_transaction()

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
        await self._migrate_star_weekly_report()

    async def _migrate_user_levels_reactions(self) -> None:
        """user_levelsテーブルにリアクションカラムを追加（既存DB用マイグレーション）"""
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

    async def _migrate_star_weekly_report(self) -> None:
        """star_settingsテーブルに週間レポート用カラムを追加（既存DB用マイグレーション）"""
        try:
            await self._db.execute(
                "ALTER TABLE star_settings ADD COLUMN weekly_report_channel_id INTEGER"
            )
            await self._db.commit()
        except Exception:
            pass

        try:
            await self._db.execute(
                "ALTER TABLE star_settings ADD COLUMN weekly_report_last_sent TIMESTAMP"
            )
            await self._db.commit()
        except Exception:
            pass
