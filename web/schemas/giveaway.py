"""
Giveaway関連のスキーマ
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GiveawayCreate(BaseModel):
    """Giveaway作成リクエスト"""
    channel_id: str = Field(..., description="投稿先チャンネルID")  # Discord Snowflake ID
    prize: str = Field(..., min_length=1, max_length=200, description="景品名")
    winner_count: int = Field(default=1, ge=1, le=20, description="当選者数")
    duration_seconds: int = Field(..., ge=60, le=2592000, description="期間（秒）60秒〜30日")


class GiveawayResponse(BaseModel):
    """Giveaway情報レスポンス"""
    id: int
    guild_id: str  # Discord Snowflake ID
    channel_id: str  # Discord Snowflake ID
    message_id: str  # Discord Snowflake ID
    host_id: str  # Discord Snowflake ID
    prize: str
    winner_count: int
    end_time: datetime
    participants: list[str]  # Discord Snowflake IDs
    winners: list[str]  # Discord Snowflake IDs
    ended: bool
    created_at: datetime

    @property
    def participant_count(self) -> int:
        return len(self.participants)


class GiveawayListItem(BaseModel):
    """Giveaway一覧アイテム"""
    id: int
    channel_id: str  # Discord Snowflake ID
    message_id: str  # Discord Snowflake ID
    prize: str
    winner_count: int
    participant_count: int
    end_time: datetime
    ended: bool
    created_at: datetime


class GiveawayListResponse(BaseModel):
    """Giveaway一覧レスポンス"""
    active: list[GiveawayListItem]
    ended: list[GiveawayListItem]
    total_active: int
    total_ended: int


class GiveawayEndResponse(BaseModel):
    """Giveaway終了レスポンス"""
    id: int
    prize: str
    winners: list[str]  # Discord Snowflake IDs
    winner_names: list[str]


class GiveawayRerollResponse(BaseModel):
    """Giveaway再抽選レスポンス"""
    id: int
    prize: str
    new_winners: list[str]  # Discord Snowflake IDs
    new_winner_names: list[str]


__all__ = [
    "GiveawayCreate",
    "GiveawayResponse",
    "GiveawayListItem",
    "GiveawayListResponse",
    "GiveawayEndResponse",
    "GiveawayRerollResponse",
]
