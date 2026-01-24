"""
ログ設定関連のデータベース操作
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import aiosqlite


class LoggerMixin:
    """ログ設定関連のデータベース操作"""

    _db: aiosqlite.Connection

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
        await self._commit()

    async def disable_logger(self, guild_id: int) -> None:
        """ログを無効化"""
        await self._db.execute(
            "UPDATE logger_settings SET enabled = 0 WHERE guild_id = ?",
            (guild_id,)
        )
        await self._commit()

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
            await self._commit()
