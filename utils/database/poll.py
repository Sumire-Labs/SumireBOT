"""
投票関連のデータベース操作
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import aiosqlite


class PollMixin:
    """投票関連のデータベース操作"""

    _db: aiosqlite.Connection

    async def create_poll(
        self,
        guild_id: int,
        channel_id: int,
        message_id: int,
        author_id: int,
        question: str,
        options: list[str],
        multi_select: bool = False,
        end_time: Optional[datetime] = None
    ) -> int:
        """投票を作成"""
        cursor = await self._db.execute("""
            INSERT INTO polls (guild_id, channel_id, message_id, author_id, question, options, multi_select, end_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            guild_id, channel_id, message_id, author_id, question,
            json.dumps(options), 1 if multi_select else 0,
            end_time.isoformat() if end_time else None
        ))
        await self._commit()
        return cursor.lastrowid

    async def get_poll(self, message_id: int) -> Optional[dict]:
        """投票を取得"""
        async with self._db.execute(
            "SELECT * FROM polls WHERE message_id = ?",
            (message_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                result = dict(row)
                result["options"] = json.loads(result.get("options", "[]"))
                result["votes"] = json.loads(result.get("votes", "{}"))
                return result
            return None

    async def get_active_polls(self) -> list[dict]:
        """終了していない投票を全て取得"""
        async with self._db.execute(
            "SELECT * FROM polls WHERE ended = 0"
        ) as cursor:
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                result = dict(row)
                result["options"] = json.loads(result.get("options", "[]"))
                result["votes"] = json.loads(result.get("votes", "{}"))
                results.append(result)
            return results

    async def vote_poll(self, message_id: int, user_id: int, option_index: int) -> bool:
        """
        投票する

        Returns:
            bool: 投票が変更されたかどうか
        """
        poll = await self.get_poll(message_id)
        if not poll or poll["ended"]:
            return False

        votes = poll["votes"]
        user_key = str(user_id)
        multi_select = bool(poll["multi_select"])

        if multi_select:
            # 複数選択: トグル
            if user_key not in votes:
                votes[user_key] = []
            if option_index in votes[user_key]:
                votes[user_key].remove(option_index)
            else:
                votes[user_key].append(option_index)
        else:
            # 単一選択: 上書き
            votes[user_key] = [option_index]

        await self._db.execute(
            "UPDATE polls SET votes = ? WHERE message_id = ?",
            (json.dumps(votes), message_id)
        )
        await self._commit()
        return True

    async def end_poll(self, message_id: int) -> None:
        """投票を終了"""
        await self._db.execute(
            "UPDATE polls SET ended = 1 WHERE message_id = ?",
            (message_id,)
        )
        await self._commit()

    async def delete_poll(self, message_id: int) -> None:
        """投票を削除"""
        await self._db.execute(
            "DELETE FROM polls WHERE message_id = ?",
            (message_id,)
        )
        await self._commit()

    # ==================== Web API用メソッド ====================

    async def get_guild_polls(self, guild_id: int, active_only: bool = False) -> list[dict]:
        """ギルドの投票一覧を取得"""
        if active_only:
            query = "SELECT * FROM polls WHERE guild_id = ? AND ended = 0 ORDER BY created_at DESC"
        else:
            query = "SELECT * FROM polls WHERE guild_id = ? ORDER BY ended ASC, created_at DESC"

        async with self._db.execute(query, (guild_id,)) as cursor:
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                result = dict(row)
                result["options"] = json.loads(result.get("options", "[]"))
                result["votes"] = json.loads(result.get("votes", "{}"))
                results.append(result)
            return results

    async def get_poll_by_id(self, poll_id: int) -> Optional[dict]:
        """IDで投票を取得"""
        async with self._db.execute(
            "SELECT * FROM polls WHERE id = ?",
            (poll_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                result = dict(row)
                result["options"] = json.loads(result.get("options", "[]"))
                result["votes"] = json.loads(result.get("votes", "{}"))
                return result
            return None

    async def end_poll_by_id(self, poll_id: int) -> None:
        """IDで投票を終了"""
        await self._db.execute(
            "UPDATE polls SET ended = 1 WHERE id = ?",
            (poll_id,)
        )
        await self._commit()
