"""
永続的View管理関連のデータベース操作
"""
from __future__ import annotations

import json
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import aiosqlite


class PersistentViewMixin:
    """永続的View管理関連のデータベース操作"""

    _db: aiosqlite.Connection

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
        await self._commit()

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
        await self._commit()
