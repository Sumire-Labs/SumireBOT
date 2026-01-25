"""
Giveaway関連のデータベース操作
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import aiosqlite


class GiveawayMixin:
    """Giveaway関連のデータベース操作"""

    _db: aiosqlite.Connection

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
        await self._commit()
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
        await self._commit()
        return True

    async def end_giveaway(self, message_id: int, winners: list[int]) -> None:
        """Giveawayを終了"""
        await self._db.execute(
            "UPDATE giveaways SET ended = 1, winners = ? WHERE message_id = ?",
            (json.dumps(winners), message_id)
        )
        await self._commit()

    async def delete_giveaway(self, message_id: int) -> None:
        """Giveawayを削除"""
        await self._db.execute(
            "DELETE FROM giveaways WHERE message_id = ?",
            (message_id,)
        )
        await self._commit()

    # ==================== Web API用メソッド ====================

    async def get_guild_giveaways(self, guild_id: int, active_only: bool = False) -> list[dict]:
        """ギルドのGiveaway一覧を取得"""
        if active_only:
            query = "SELECT * FROM giveaways WHERE guild_id = ? AND ended = 0 ORDER BY end_time ASC"
        else:
            query = "SELECT * FROM giveaways WHERE guild_id = ? ORDER BY ended ASC, end_time DESC"

        async with self._db.execute(query, (guild_id,)) as cursor:
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                result = dict(row)
                result["participants"] = json.loads(result.get("participants", "[]"))
                result["winners"] = json.loads(result.get("winners", "[]"))
                results.append(result)
            return results

    async def get_giveaway_by_id(self, giveaway_id: int) -> Optional[dict]:
        """IDでGiveawayを取得"""
        async with self._db.execute(
            "SELECT * FROM giveaways WHERE id = ?",
            (giveaway_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                result = dict(row)
                result["participants"] = json.loads(result.get("participants", "[]"))
                result["winners"] = json.loads(result.get("winners", "[]"))
                return result
            return None

    async def update_giveaway_winners(self, giveaway_id: int, winners: list[int]) -> None:
        """Giveawayの当選者を更新（再抽選用）"""
        await self._db.execute(
            "UPDATE giveaways SET winners = ? WHERE id = ?",
            (json.dumps(winners), giveaway_id)
        )
        await self._commit()

    async def end_giveaway_by_id(self, giveaway_id: int, winners: list[int]) -> None:
        """IDでGiveawayを終了"""
        await self._db.execute(
            "UPDATE giveaways SET ended = 1, winners = ? WHERE id = ?",
            (json.dumps(winners), giveaway_id)
        )
        await self._commit()
