"""
ランキング関連のスキーマ
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class UserRankInfo(BaseModel):
    """ユーザーランキング情報（共通）"""
    rank: int
    user_id: str  # Discord Snowflake ID (string to avoid JS precision loss)
    username: str
    display_name: str
    avatar_url: Optional[str] = None


# ==================== レベルランキング ====================

class LevelRankEntry(UserRankInfo):
    """レベルランキングエントリー"""
    level: int
    xp: int
    total_xp: int


class LevelLeaderboardResponse(BaseModel):
    """レベルランキングレスポンス"""
    entries: list[LevelRankEntry]
    total_users: int


# ==================== VCランキング ====================

class VCRankEntry(UserRankInfo):
    """VCランキングエントリー"""
    vc_time: int  # 秒
    vc_level: int


class VCLeaderboardResponse(BaseModel):
    """VCランキングレスポンス"""
    entries: list[VCRankEntry]
    total_users: int


# ==================== スターランキング ====================

class StarUserRankEntry(UserRankInfo):
    """スターランキング（ユーザー別）エントリー"""
    star_count: int
    message_count: int


class StarMessageRankEntry(BaseModel):
    """スターランキング（メッセージ別）エントリー"""
    rank: int
    message_id: str  # Discord Snowflake ID
    channel_id: str  # Discord Snowflake ID
    author_id: str  # Discord Snowflake ID
    author_name: str
    star_count: int


class StarLeaderboardResponse(BaseModel):
    """スターランキングレスポンス"""
    by_user: list[StarUserRankEntry]
    by_message: list[StarMessageRankEntry]
    total_users: int
    total_messages: int


# ==================== 単語カウンターランキング ====================

class WordCountRankEntry(UserRankInfo):
    """単語カウンターランキングエントリー"""
    word: str
    count: int


class WordLeaderboardResponse(BaseModel):
    """単語別ランキングレスポンス"""
    word: str
    entries: list[WordCountRankEntry]
    total_users: int


class WordListResponse(BaseModel):
    """追跡中の単語一覧レスポンス"""
    words: list[str]


# ==================== リアクションランキング ====================

class ReactionRankEntry(UserRankInfo):
    """リアクションランキングエントリー"""
    reactions_given: int
    reactions_received: int


class ReactionLeaderboardResponse(BaseModel):
    """リアクションランキングレスポンス"""
    by_given: list[ReactionRankEntry]
    by_received: list[ReactionRankEntry]
    total_users: int


__all__ = [
    "UserRankInfo",
    "LevelRankEntry",
    "LevelLeaderboardResponse",
    "VCRankEntry",
    "VCLeaderboardResponse",
    "StarUserRankEntry",
    "StarMessageRankEntry",
    "StarLeaderboardResponse",
    "WordCountRankEntry",
    "WordLeaderboardResponse",
    "WordListResponse",
    "ReactionRankEntry",
    "ReactionLeaderboardResponse",
]
