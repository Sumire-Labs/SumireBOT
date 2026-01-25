"""
Webセッション関連のデータベース操作
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import aiosqlite


class WebSessionMixin:
    """Webセッション関連のデータベース操作"""

    _db: aiosqlite.Connection

    async def create_web_session(
        self,
        user_id: int,
        session_token: str,
        access_token: str,
        refresh_token: Optional[str],
        expires_at: datetime
    ) -> int:
        """Webセッションを作成"""
        cursor = await self._db.execute(
            """
            INSERT INTO web_sessions (user_id, session_token, access_token, refresh_token, expires_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, session_token, access_token, refresh_token, expires_at.isoformat())
        )
        await self._commit()
        return cursor.lastrowid

    async def get_web_session(self, session_token: str) -> Optional[dict]:
        """セッショントークンからセッション情報を取得"""
        async with self._db.execute(
            """
            SELECT id, user_id, session_token, access_token, refresh_token,
                   expires_at, created_at, last_used_at
            FROM web_sessions
            WHERE session_token = ?
            """,
            (session_token,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def get_user_sessions(self, user_id: int) -> list[dict]:
        """ユーザーの全セッションを取得"""
        async with self._db.execute(
            """
            SELECT id, user_id, session_token, access_token, refresh_token,
                   expires_at, created_at, last_used_at
            FROM web_sessions
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def update_web_session(
        self,
        session_token: str,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> None:
        """セッション情報を更新"""
        updates = ["last_used_at = CURRENT_TIMESTAMP"]
        params = []

        if access_token is not None:
            updates.append("access_token = ?")
            params.append(access_token)
        if refresh_token is not None:
            updates.append("refresh_token = ?")
            params.append(refresh_token)
        if expires_at is not None:
            updates.append("expires_at = ?")
            params.append(expires_at.isoformat())

        params.append(session_token)

        await self._db.execute(
            f"UPDATE web_sessions SET {', '.join(updates)} WHERE session_token = ?",
            params
        )
        await self._commit()

    async def update_session_last_used(self, session_token: str) -> None:
        """セッションの最終使用日時を更新"""
        await self._db.execute(
            "UPDATE web_sessions SET last_used_at = CURRENT_TIMESTAMP WHERE session_token = ?",
            (session_token,)
        )
        await self._commit()

    async def delete_web_session(self, session_token: str) -> None:
        """セッションを削除"""
        await self._db.execute(
            "DELETE FROM web_sessions WHERE session_token = ?",
            (session_token,)
        )
        await self._commit()

    async def delete_user_sessions(self, user_id: int) -> int:
        """ユーザーの全セッションを削除"""
        cursor = await self._db.execute(
            "DELETE FROM web_sessions WHERE user_id = ?",
            (user_id,)
        )
        await self._commit()
        return cursor.rowcount

    async def cleanup_expired_sessions(self) -> int:
        """期限切れセッションを削除"""
        cursor = await self._db.execute(
            "DELETE FROM web_sessions WHERE expires_at < datetime('now')"
        )
        await self._commit()
        return cursor.rowcount

    async def is_session_valid(self, session_token: str) -> bool:
        """セッションが有効かどうかを確認"""
        async with self._db.execute(
            """
            SELECT 1 FROM web_sessions
            WHERE session_token = ? AND expires_at > datetime('now')
            """,
            (session_token,)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None
