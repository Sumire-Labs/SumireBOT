"""
認証API エンドポイント
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from utils.config import Config
from utils.database import Database
from utils.logging import get_logger
from web.auth.dependencies import (
    SESSION_COOKIE_NAME,
    get_config,
    get_current_user,
    get_current_user_optional,
    get_db,
    get_session_token,
)
from web.auth.models import User
from web.auth.oauth import get_oauth

logger = get_logger("sumire.web.api.auth")

auth_router = APIRouter()

# OAuth state を一時保存（本番ではRedisなどを使用）
_oauth_states: dict[str, datetime] = {}


class UserResponse(BaseModel):
    """ユーザー情報レスポンス"""
    id: int
    username: str
    display_name: str
    avatar_url: str


class LoginResponse(BaseModel):
    """ログインレスポンス"""
    url: str


@auth_router.get("/login")
async def login(
    redirect: Optional[str] = None,
    config: Config = Depends(get_config),
) -> RedirectResponse:
    """
    Discord OAuth2 ログイン

    Discord認証ページにリダイレクト
    """
    oauth = get_oauth()

    # stateを生成（CSRF対策）
    state = oauth.generate_state()
    _oauth_states[state] = datetime.now()

    # 古いstateを削除（5分以上前のもの）
    cutoff = datetime.now() - timedelta(minutes=5)
    expired_states = [s for s, t in _oauth_states.items() if t < cutoff]
    for s in expired_states:
        del _oauth_states[s]

    url = oauth.get_authorization_url(state)
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@auth_router.get("/callback")
async def callback(
    code: str,
    state: str,
    request: Request,
    db: Database = Depends(get_db),
    config: Config = Depends(get_config),
) -> RedirectResponse:
    """
    Discord OAuth2 コールバック

    認証コードを受け取り、セッションを作成してダッシュボードにリダイレクト
    """
    # stateの検証
    if state not in _oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無効なstateです",
        )
    del _oauth_states[state]

    oauth = get_oauth()

    # 認証コードをトークンに交換
    token_response = await oauth.exchange_code(code)
    if not token_response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="認証に失敗しました",
        )

    # ユーザー情報を取得
    user = await oauth.get_user(token_response.access_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ユーザー情報の取得に失敗しました",
        )

    # セッションを作成
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(seconds=config.web_session_max_age)

    await db.create_web_session(
        user_id=user.id,
        session_token=session_token,
        access_token=token_response.access_token,
        refresh_token=token_response.refresh_token,
        expires_at=expires_at,
    )

    logger.info(f"ユーザーがログインしました: {user.username} (ID: {user.id})")

    # ダッシュボードにリダイレクト
    # 開発時はフロントエンドURL、本番時はbase_urlを使用
    frontend_url = config.get("web", "frontend_url", default=None)
    if frontend_url:
        redirect_url = f"{frontend_url}/dashboard"
    else:
        redirect_url = "/dashboard"

    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

    # セッションCookieを設定
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=config.web_session_max_age,
        httponly=True,
        samesite="lax",
        secure=config.web_base_url.startswith("https"),
    )

    return response


@auth_router.post("/logout")
async def logout(
    response: Response,
    db: Database = Depends(get_db),
    session_token: Optional[str] = Depends(get_session_token),
) -> dict:
    """
    ログアウト

    セッションを削除してCookieをクリア
    """
    if session_token:
        await db.delete_web_session(session_token)

    response.delete_cookie(key=SESSION_COOKIE_NAME)

    return {"message": "ログアウトしました"}


@auth_router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(get_current_user),
) -> UserResponse:
    """
    現在のログインユーザー情報を取得
    """
    return UserResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
    )


@auth_router.get("/check")
async def check_auth(
    user: Optional[User] = Depends(get_current_user_optional),
) -> dict:
    """
    認証状態を確認

    ログイン済みならユーザー情報、未ログインならnullを返す
    """
    if user:
        return {
            "authenticated": True,
            "user": UserResponse(
                id=user.id,
                username=user.username,
                display_name=user.display_name,
                avatar_url=user.avatar_url,
            ),
        }
    return {"authenticated": False, "user": None}
