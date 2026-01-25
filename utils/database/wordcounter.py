"""
単語カウンター関連のデータベース操作
"""
from __future__ import annotations

import json
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import aiosqlite


class WordCounterMixin:
    """単語カウンター関連のデータベース操作"""

    _db: aiosqlite.Connection

    # ==================== 設定 ====================

    async def get_wordcounter_settings(self, guild_id: int) -> Optional[dict]:
        """単語カウンター設定を取得"""
        async with self._db.execute(
            "SELECT * FROM wordcounter_settings WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                result = dict(row)
                result["words"] = json.loads(result.get("words", "[]"))
                result["milestones"] = json.loads(result.get("milestones", "[10,50,100,200,300,500,1000]"))
                return result
            return None

    async def set_wordcounter_enabled(self, guild_id: int, enabled: bool) -> None:
        """単語カウンター機能の有効/無効を設定"""
        await self._db.execute("""
            INSERT INTO wordcounter_settings (guild_id, enabled)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                enabled = excluded.enabled
        """, (guild_id, 1 if enabled else 0))
        await self._commit()

    async def add_counter_word(self, guild_id: int, word: str) -> bool:
        """カウント対象の単語を追加

        Returns:
            bool: 追加された場合True、既に存在する場合False
        """
        settings = await self.get_wordcounter_settings(guild_id)
        words = settings.get("words", []) if settings else []

        if word in words:
            return False

        words.append(word)
        await self._db.execute("""
            INSERT INTO wordcounter_settings (guild_id, words)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                words = excluded.words
        """, (guild_id, json.dumps(words)))
        await self._commit()
        return True

    async def remove_counter_word(self, guild_id: int, word: str) -> bool:
        """カウント対象の単語を削除

        Returns:
            bool: 削除された場合True、存在しなかった場合False
        """
        settings = await self.get_wordcounter_settings(guild_id)
        if not settings:
            return False

        words = settings.get("words", [])
        if word not in words:
            return False

        words.remove(word)
        await self._db.execute(
            "UPDATE wordcounter_settings SET words = ? WHERE guild_id = ?",
            (json.dumps(words), guild_id)
        )
        await self._commit()
        return True

    async def clear_counter_words(self, guild_id: int) -> None:
        """すべてのカウント対象単語を削除"""
        await self._db.execute(
            "UPDATE wordcounter_settings SET words = '[]' WHERE guild_id = ?",
            (guild_id,)
        )
        await self._commit()

    # ==================== カウント操作 ====================

    async def increment_word_count(
        self,
        guild_id: int,
        user_id: int,
        word: str,
        amount: int = 1
    ) -> int:
        """
        単語カウントを増加させる

        Returns:
            int: 更新後の合計カウント
        """
        await self._db.execute("""
            INSERT INTO wordcounter_counts (guild_id, user_id, word, count, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id, user_id, word) DO UPDATE SET
                count = wordcounter_counts.count + ?,
                updated_at = CURRENT_TIMESTAMP
        """, (guild_id, user_id, word, amount, amount))
        await self._commit()

        # 更新後のカウントを取得
        async with self._db.execute(
            "SELECT count FROM wordcounter_counts WHERE guild_id = ? AND user_id = ? AND word = ?",
            (guild_id, user_id, word)
        ) as cursor:
            row = await cursor.fetchone()
            return row["count"] if row else amount

    async def get_user_word_count(
        self,
        guild_id: int,
        user_id: int,
        word: str
    ) -> Optional[dict]:
        """ユーザーの特定単語のカウント情報を取得"""
        async with self._db.execute(
            "SELECT * FROM wordcounter_counts WHERE guild_id = ? AND user_id = ? AND word = ?",
            (guild_id, user_id, word)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_last_milestone(
        self,
        guild_id: int,
        user_id: int,
        word: str,
        milestone: int
    ) -> None:
        """最後に通知したマイルストーンを更新"""
        await self._db.execute(
            "UPDATE wordcounter_counts SET last_milestone = ? WHERE guild_id = ? AND user_id = ? AND word = ?",
            (milestone, guild_id, user_id, word)
        )
        await self._commit()

    # ==================== ランキング ====================

    async def get_word_leaderboard(
        self,
        guild_id: int,
        word: str,
        limit: int = 10
    ) -> list[dict]:
        """単語別ランキングを取得"""
        async with self._db.execute("""
            SELECT user_id, count
            FROM wordcounter_counts
            WHERE guild_id = ? AND word = ? AND count > 0
            ORDER BY count DESC
            LIMIT ?
        """, (guild_id, word, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_user_word_totals(
        self,
        guild_id: int,
        user_id: int
    ) -> list[dict]:
        """ユーザーの全単語カウント一覧を取得"""
        async with self._db.execute("""
            SELECT word, count
            FROM wordcounter_counts
            WHERE guild_id = ? AND user_id = ? AND count > 0
            ORDER BY count DESC
        """, (guild_id, user_id)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_all_words_leaderboard(
        self,
        guild_id: int,
        limit: int = 10
    ) -> list[dict]:
        """全単語の合計カウントランキングを取得"""
        async with self._db.execute("""
            SELECT user_id, SUM(count) as total_count
            FROM wordcounter_counts
            WHERE guild_id = ?
            GROUP BY user_id
            HAVING total_count > 0
            ORDER BY total_count DESC
            LIMIT ?
        """, (guild_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
