"""
Discord OAuth2 認証
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

import httpx

from utils.config import Config
from utils.logging import get_logger
from .models import User, Guild, TokenResponse

logger = get_logger("sumire.web.auth")


class DiscordOAuth:
    """Discord OAuth2 クライアント"""

    AUTHORIZE_URL = "https://discord.com/api/oauth2/authorize"
    TOKEN_URL = "https://discord.com/api/oauth2/token"
    API_BASE = "https://discord.com/api/v10"
    SCOPES = ["identify", "guilds"]

    def __init__(self) -> None:
        self.config = Config()
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def client_id(self) -> str:
        return self.config.oauth_client_id

    @property
    def client_secret(self) -> str:
        return self.config.oauth_client_secret

    @property
    def redirect_uri(self) -> str:
        return f"{self.config.web_base_url}/api/auth/callback"

    async def _get_client(self) -> httpx.AsyncClient:
        """HTTPクライアントを取得"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=10.0)
        return self._http_client

    async def close(self) -> None:
        """HTTPクライアントを閉じる"""
        if self._http_client:
            await self._http_client.aclose()

    def generate_state(self) -> str:
        """CSRF対策用のstateを生成"""
        return secrets.token_urlsafe(32)

    def get_authorization_url(self, state: str) -> str:
        """OAuth2認証URLを生成"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "state": state,
        }
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> Optional[TokenResponse]:
        """認証コードをトークンに交換"""
        client = await self._get_client()

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        try:
            response = await client.post(
                self.TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return None

            return TokenResponse(**response.json())

        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            return None

    async def refresh_token(self, refresh_token: str) -> Optional[TokenResponse]:
        """リフレッシュトークンでアクセストークンを更新"""
        client = await self._get_client()

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        try:
            response = await client.post(
                self.TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                logger.error(f"Token refresh failed: {response.status_code}")
                return None

            return TokenResponse(**response.json())

        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None

    async def get_user(self, access_token: str) -> Optional[User]:
        """ユーザー情報を取得"""
        client = await self._get_client()

        try:
            response = await client.get(
                f"{self.API_BASE}/users/@me",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                logger.error(f"Get user failed: {response.status_code}")
                return None

            data = response.json()
            return User(
                id=int(data["id"]),
                username=data["username"],
                discriminator=data.get("discriminator", "0"),
                avatar=data.get("avatar"),
                global_name=data.get("global_name"),
            )

        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None

    async def get_user_guilds(self, access_token: str) -> list[Guild]:
        """ユーザーが所属するギルド一覧を取得"""
        client = await self._get_client()

        try:
            response = await client.get(
                f"{self.API_BASE}/users/@me/guilds",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                logger.error(f"Get guilds failed: {response.status_code}")
                return []

            guilds = []
            for data in response.json():
                guilds.append(Guild(
                    id=int(data["id"]),
                    name=data["name"],
                    icon=data.get("icon"),
                    owner=data.get("owner", False),
                    permissions=int(data.get("permissions", 0)),
                ))
            return guilds

        except Exception as e:
            logger.error(f"Get guilds error: {e}")
            return []

    async def revoke_token(self, token: str) -> bool:
        """トークンを無効化"""
        client = await self._get_client()

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "token": token,
        }

        try:
            response = await client.post(
                f"{self.API_BASE}/oauth2/token/revoke",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Token revoke error: {e}")
            return False


# シングルトンインスタンス
_oauth_instance: Optional[DiscordOAuth] = None


def get_oauth() -> DiscordOAuth:
    """OAuth クライアントを取得"""
    global _oauth_instance
    if _oauth_instance is None:
        _oauth_instance = DiscordOAuth()
    return _oauth_instance
