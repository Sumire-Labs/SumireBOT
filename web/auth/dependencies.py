"""
FastAPI 認証依存関係
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from fastapi import Cookie, Depends, HTTPException, Request, status

from utils.config import Config
from utils.database import Database
from utils.logging import get_logger
from .models import User
from .oauth import get_oauth

if TYPE_CHECKING:
    import discord
    from bot import SumireBot

logger = get_logger("sumire.web.auth")

SESSION_COOKIE_NAME = "sumire_session"


def get_bot(request: Request) -> "SumireBot":
    """BotインスタンスをRequestから取得"""
    return request.app.state.bot


def get_db(request: Request) -> Database:
    """DatabaseインスタンスをRequestから取得"""
    return request.app.state.db


def get_config(request: Request) -> Config:
    """ConfigインスタンスをRequestから取得"""
    return request.app.state.config


async def get_current_user(
    request: Request,
    session_token: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> User:
    """
    現在のログインユーザーを取得（必須）

    セッションが無効な場合は401エラーを返す
    """
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証が必要です",
        )

    db = get_db(request)
    session = await db.get_web_session(session_token)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="セッションが無効です",
        )

    # 有効期限チェック
    expires_at = datetime.fromisoformat(session["expires_at"])
    if expires_at < datetime.now():
        await db.delete_web_session(session_token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="セッションの有効期限が切れています",
        )

    # 最終使用日時を更新
    await db.update_session_last_used(session_token)

    # ユーザー情報を取得
    oauth = get_oauth()
    user = await oauth.get_user(session["access_token"])

    if not user:
        # アクセストークンが無効な場合はリフレッシュを試みる
        if session.get("refresh_token"):
            token_response = await oauth.refresh_token(session["refresh_token"])
            if token_response:
                # 新しいトークンを保存
                await db.update_web_session(
                    session_token,
                    access_token=token_response.access_token,
                    refresh_token=token_response.refresh_token,
                )
                user = await oauth.get_user(token_response.access_token)

    if not user:
        await db.delete_web_session(session_token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー情報の取得に失敗しました",
        )

    return user


async def get_current_user_optional(
    request: Request,
    session_token: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> Optional[User]:
    """
    現在のログインユーザーを取得（任意）

    未ログインの場合はNoneを返す
    """
    if not session_token:
        return None

    try:
        return await get_current_user(request, session_token)
    except HTTPException:
        return None


async def require_guild_admin(
    guild_id: int,
    user: User = Depends(get_current_user),
    bot: "SumireBot" = Depends(get_bot),
) -> "discord.Guild":
    """
    ギルド管理権限を要求

    ユーザーがギルドの管理権限を持っていない場合は403エラーを返す
    """
    logger.info(f"require_guild_admin: guild_id={guild_id}, type={type(guild_id)}")
    logger.info(f"Bot guilds: {[g.id for g in bot.guilds]}")

    guild = bot.get_guild(guild_id)

    if not guild:
        logger.warning(f"Guild not found: {guild_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"サーバーが見つかりません (ID: {guild_id})",
        )

    member = guild.get_member(user.id)

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このサーバーのメンバーではありません",
        )

    if not member.guild_permissions.manage_guild and not member.guild_permissions.administrator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="サーバー管理権限がありません",
        )

    return guild


async def get_session_token(
    session_token: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> Optional[str]:
    """セッショントークンを取得"""
    return session_token
