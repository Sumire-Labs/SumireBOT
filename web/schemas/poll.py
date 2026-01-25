"""
Poll関連のスキーマ
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PollOption(BaseModel):
    """投票オプション"""
    label: str = Field(..., min_length=1, max_length=100)
    emoji: Optional[str] = None


class PollCreate(BaseModel):
    """Poll作成リクエスト"""
    channel_id: int = Field(..., description="投稿先チャンネルID")
    question: str = Field(..., min_length=1, max_length=300, description="質問文")
    options: list[str] = Field(..., min_length=2, max_length=10, description="選択肢（2〜10個）")
    multi_select: bool = Field(default=False, description="複数選択を許可")
    duration_seconds: Optional[int] = Field(default=None, ge=60, le=2592000, description="期間（秒）、nullの場合は無期限")


class PollVoteResult(BaseModel):
    """投票結果"""
    option: str
    count: int
    percentage: float
    voters: list[int]


class PollResponse(BaseModel):
    """Poll情報レスポンス"""
    id: int
    guild_id: int
    channel_id: int
    message_id: int
    author_id: int
    question: str
    options: list[str]
    votes: dict[str, list[int]]  # option -> user_ids
    multi_select: bool
    end_time: Optional[datetime]
    ended: bool
    created_at: datetime

    @property
    def total_votes(self) -> int:
        return sum(len(v) for v in self.votes.values())


class PollListItem(BaseModel):
    """Poll一覧アイテム"""
    id: int
    channel_id: int
    message_id: int
    question: str
    option_count: int
    total_votes: int
    multi_select: bool
    end_time: Optional[datetime]
    ended: bool
    created_at: datetime


class PollListResponse(BaseModel):
    """Poll一覧レスポンス"""
    active: list[PollListItem]
    ended: list[PollListItem]
    total_active: int
    total_ended: int


class PollResultResponse(BaseModel):
    """Poll結果レスポンス"""
    id: int
    question: str
    results: list[PollVoteResult]
    total_votes: int
    ended: bool


__all__ = [
    "PollOption",
    "PollCreate",
    "PollVoteResult",
    "PollResponse",
    "PollListItem",
    "PollListResponse",
    "PollResultResponse",
]
