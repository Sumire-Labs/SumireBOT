"""
音楽設定関連のデータベース操作
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import aiosqlite


class MusicMixin:
    """音楽設定関連のデータベース操作"""

    _db: aiosqlite.Connection

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
        await self._commit()
