"""
ギルド設定関連のデータベース操作
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import aiosqlite


class GuildMixin:
    """ギルド設定関連のデータベース操作"""

    _db: aiosqlite.Connection

    async def ensure_guild(self, guild_id: int) -> None:
        """サーバー設定が存在することを保証"""
        await self._db.execute(
            "INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)",
            (guild_id,)
        )
        await self._commit()

    async def get_guild_language(self, guild_id: int) -> str:
        """サーバーの言語設定を取得"""
        await self.ensure_guild(guild_id)
        async with self._db.execute(
            "SELECT language FROM guild_settings WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row["language"] if row else "ja"
