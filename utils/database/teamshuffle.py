"""
チーム分けくじ関連のデータベース操作
"""
from __future__ import annotations

import json
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import aiosqlite


class TeamShuffleMixin:
    """チーム分けくじ関連のデータベース操作"""

    _db: aiosqlite.Connection

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
        await self._commit()
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
        await self._commit()
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
        await self._commit()
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
        await self._commit()
        return True

    async def delete_team_shuffle_panel(self, message_id: int) -> None:
        """チーム分けくじパネルを削除"""
        await self._db.execute(
            "DELETE FROM team_shuffle_panels WHERE message_id = ?",
            (message_id,)
        )
        await self._commit()
