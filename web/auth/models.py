"""
認証関連のモデル
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    """Discordユーザー情報"""
    id: int
    username: str
    discriminator: str
    avatar: Optional[str] = None
    global_name: Optional[str] = None

    @property
    def display_name(self) -> str:
        """表示名を取得"""
        return self.global_name or self.username

    @property
    def avatar_url(self) -> str:
        """アバターURLを取得"""
        if self.avatar:
            return f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar}.png"
        # デフォルトアバター
        default_avatar_index = (self.id >> 22) % 6
        return f"https://cdn.discordapp.com/embed/avatars/{default_avatar_index}.png"


class Guild(BaseModel):
    """Discordギルド情報"""
    id: int
    name: str
    icon: Optional[str] = None
    owner: bool = False
    permissions: int = 0

    @property
    def icon_url(self) -> Optional[str]:
        """アイコンURLを取得"""
        if self.icon:
            return f"https://cdn.discordapp.com/icons/{self.id}/{self.icon}.png"
        return None

    @property
    def has_manage_guild(self) -> bool:
        """サーバー管理権限があるか"""
        MANAGE_GUILD = 0x20  # 1 << 5
        return (self.permissions & MANAGE_GUILD) == MANAGE_GUILD or self.owner


class SessionData(BaseModel):
    """セッションデータ"""
    user_id: int
    session_token: str
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: datetime
    created_at: datetime
    last_used_at: datetime


class TokenResponse(BaseModel):
    """Discord OAuth2 トークンレスポンス"""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: str


class AuthState(BaseModel):
    """OAuth2 認証状態（CSRF対策）"""
    state: str
    redirect_uri: Optional[str] = None
    created_at: datetime
