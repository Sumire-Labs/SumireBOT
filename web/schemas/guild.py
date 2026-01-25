"""
ギルド関連のスキーマ
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


# ==================== ギルド基本情報 ====================

class GuildInfo(BaseModel):
    """ギルド基本情報"""
    id: str  # Discord Snowflake ID (string to avoid JS precision loss)
    name: str
    icon_url: Optional[str] = None
    member_count: int
    bot_joined: bool = True


class GuildListItem(BaseModel):
    """ギルド一覧アイテム"""
    id: str  # Discord Snowflake ID (string to avoid JS precision loss)
    name: str
    icon_url: Optional[str] = None
    has_manage_permission: bool
    bot_joined: bool


class ChannelInfo(BaseModel):
    """チャンネル情報"""
    id: str  # Discord Snowflake ID (string to avoid JS precision loss)
    name: str
    type: str  # "text", "voice", "category"


class RoleInfo(BaseModel):
    """ロール情報"""
    id: str  # Discord Snowflake ID (string to avoid JS precision loss)
    name: str
    color: int
    position: int


# ==================== 機能別設定 ====================

class LevelingSettings(BaseModel):
    """レベリング設定"""
    enabled: bool = True
    ignored_channels: list[str] = []  # Discord Snowflake IDs


class LevelingSettingsUpdate(BaseModel):
    """レベリング設定更新"""
    enabled: Optional[bool] = None
    ignored_channels: Optional[list[str]] = None


class StarSettings(BaseModel):
    """スター設定"""
    enabled: bool = True
    target_channels: list[str] = []  # Discord Snowflake IDs
    weekly_report_channel_id: Optional[str] = None


class StarSettingsUpdate(BaseModel):
    """スター設定更新"""
    enabled: Optional[bool] = None
    target_channels: Optional[list[str]] = None
    weekly_report_channel_id: Optional[str] = None


class WordCounterSettings(BaseModel):
    """単語カウンター設定"""
    enabled: bool = True
    words: list[str] = []
    milestones: list[int] = [10, 50, 100, 200, 300, 500, 1000]


class WordCounterSettingsUpdate(BaseModel):
    """単語カウンター設定更新"""
    enabled: Optional[bool] = None
    words: Optional[list[str]] = None
    milestones: Optional[list[int]] = None


class LoggerSettings(BaseModel):
    """ロガー設定"""
    enabled: bool = False
    channel_id: Optional[str] = None  # Discord Snowflake ID
    log_messages: bool = True
    log_channels: bool = True
    log_roles: bool = True
    log_members: bool = True


class LoggerSettingsUpdate(BaseModel):
    """ロガー設定更新"""
    enabled: Optional[bool] = None
    channel_id: Optional[str] = None
    log_messages: Optional[bool] = None
    log_channels: Optional[bool] = None
    log_roles: Optional[bool] = None
    log_members: Optional[bool] = None


class AutoroleSettings(BaseModel):
    """自動ロール設定"""
    enabled: bool = True
    human_role_id: Optional[str] = None  # Discord Snowflake ID
    bot_role_id: Optional[str] = None  # Discord Snowflake ID


class AutoroleSettingsUpdate(BaseModel):
    """自動ロール設定更新"""
    enabled: Optional[bool] = None
    human_role_id: Optional[str] = None
    bot_role_id: Optional[str] = None


class TicketSettings(BaseModel):
    """チケット設定"""
    category_id: Optional[str] = None  # Discord Snowflake ID
    panel_channel_id: Optional[str] = None  # Discord Snowflake ID
    panel_message_id: Optional[str] = None  # Discord Snowflake ID
    ticket_counter: int = 0


class MusicSettings(BaseModel):
    """音楽設定"""
    default_volume: int = 50
    dj_role_id: Optional[str] = None  # Discord Snowflake ID
    music_channel_id: Optional[str] = None  # Discord Snowflake ID


class MusicSettingsUpdate(BaseModel):
    """音楽設定更新"""
    default_volume: Optional[int] = None
    dj_role_id: Optional[str] = None
    music_channel_id: Optional[str] = None


# ==================== 全設定まとめ ====================

class GuildSettings(BaseModel):
    """ギルド全設定"""
    leveling: LevelingSettings
    star: StarSettings
    wordcounter: WordCounterSettings
    logger: LoggerSettings
    autorole: AutoroleSettings
    ticket: TicketSettings
    music: MusicSettings


class GuildDetailResponse(BaseModel):
    """ギルド詳細レスポンス"""
    info: GuildInfo
    channels: list[ChannelInfo]
    roles: list[RoleInfo]
    settings: GuildSettings


__all__ = [
    "GuildInfo",
    "GuildListItem",
    "ChannelInfo",
    "RoleInfo",
    "LevelingSettings",
    "LevelingSettingsUpdate",
    "StarSettings",
    "StarSettingsUpdate",
    "WordCounterSettings",
    "WordCounterSettingsUpdate",
    "LoggerSettings",
    "LoggerSettingsUpdate",
    "AutoroleSettings",
    "AutoroleSettingsUpdate",
    "TicketSettings",
    "MusicSettings",
    "MusicSettingsUpdate",
    "GuildSettings",
    "GuildDetailResponse",
]
