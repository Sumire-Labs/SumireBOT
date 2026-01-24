"""
自動ロール設定関連のデータベース操作
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import aiosqlite


class AutoroleMixin:
    """自動ロール設定関連のデータベース操作"""

    _db: aiosqlite.Connection

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
        current = await self.get_autorole_settings(guild_id)

        if current:
            new_human = human_role_id if human_role_id is not None else current.get("human_role_id")
            new_bot = bot_role_id if bot_role_id is not None else current.get("bot_role_id")
            new_enabled = (1 if enabled else 0) if enabled is not None else current.get("enabled", 1)

            await self._db.execute("""
                UPDATE autorole_settings
                SET human_role_id = ?, bot_role_id = ?, enabled = ?
                WHERE guild_id = ?
            """, (new_human, new_bot, new_enabled, guild_id))
        else:
            await self._db.execute("""
                INSERT INTO autorole_settings (guild_id, human_role_id, bot_role_id, enabled)
                VALUES (?, ?, ?, ?)
            """, (guild_id, human_role_id, bot_role_id, 1 if enabled is None else (1 if enabled else 0)))

        await self._commit()

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
        await self._commit()
