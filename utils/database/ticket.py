"""
チケットシステム関連のデータベース操作
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import aiosqlite


class TicketMixin:
    """チケットシステム関連のデータベース操作"""

    _db: aiosqlite.Connection

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
        await self._commit()

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
        await self._commit()
        return next_number

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
        await self._commit()
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
        await self._commit()

    async def update_ticket_category(self, channel_id: int, category: str) -> None:
        """チケットのカテゴリを更新"""
        await self._db.execute(
            "UPDATE tickets SET category = ? WHERE channel_id = ?",
            (category, channel_id)
        )
        await self._commit()

    async def get_user_open_tickets(self, guild_id: int, user_id: int) -> list[dict]:
        """ユーザーのオープンなチケットを取得"""
        async with self._db.execute(
            "SELECT * FROM tickets WHERE guild_id = ? AND user_id = ? AND status != 'closed'",
            (guild_id, user_id)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
