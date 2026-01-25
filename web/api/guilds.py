"""
ギルドAPI エンドポイント
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

import discord
from fastapi import APIRouter, Depends, HTTPException, status

from utils.database import Database
from utils.logging import get_logger
from web.auth.dependencies import get_bot, get_current_user, get_db, get_session_token, require_guild_admin, SESSION_COOKIE_NAME
from web.auth.models import User
from web.auth.oauth import get_oauth
from fastapi import Cookie
from typing import Optional
from web.schemas.guild import (
    AutoroleSettings,
    AutoroleSettingsUpdate,
    ChannelInfo,
    GuildDetailResponse,
    GuildInfo,
    GuildListItem,
    GuildSettings,
    LevelingSettings,
    LevelingSettingsUpdate,
    LoggerSettings,
    LoggerSettingsUpdate,
    MusicSettings,
    MusicSettingsUpdate,
    RoleInfo,
    StarSettings,
    StarSettingsUpdate,
    TicketSettings,
    WordCounterSettings,
    WordCounterSettingsUpdate,
)

if TYPE_CHECKING:
    from bot import SumireBot

logger = get_logger("sumire.web.api.guilds")

guilds_router = APIRouter()


# ==================== ギルド一覧・情報 ====================

@guilds_router.get("", response_model=list[GuildListItem])
async def get_guilds(
    user: User = Depends(get_current_user),
    bot: "SumireBot" = Depends(get_bot),
    db: Database = Depends(get_db),
    session_token: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> list[GuildListItem]:
    """
    ユーザーがアクセス可能なギルド一覧を取得

    Botが参加しているギルドのうち、ユーザーが管理権限を持つものを返す
    """
    oauth = get_oauth()

    # セッションからアクセストークンを取得
    session = await db.get_web_session(session_token) if session_token else None

    # ユーザーのギルド一覧をDiscord APIから取得
    user_guilds = await oauth.get_user_guilds(session["access_token"]) if session else []

    # Botが参加しているギルドIDセット
    bot_guild_ids = {g.id for g in bot.guilds}
    logger.info(f"Bot guild IDs: {bot_guild_ids}")

    guilds = []
    for guild in user_guilds:
        logger.info(f"User guild: id={guild.id}, name={guild.name}, manage={guild.has_manage_guild}, bot_joined={guild.id in bot_guild_ids}")
        if guild.has_manage_guild:
            guilds.append(GuildListItem(
                id=guild.id,
                name=guild.name,
                icon_url=guild.icon_url,
                has_manage_permission=True,
                bot_joined=guild.id in bot_guild_ids,
            ))

    return guilds


@guilds_router.get("/{guild_id}", response_model=GuildDetailResponse)
async def get_guild(
    guild: discord.Guild = Depends(require_guild_admin),
    db: Database = Depends(get_db),
) -> GuildDetailResponse:
    """
    ギルド詳細情報を取得
    """
    # チャンネル一覧
    channels = []
    for channel in guild.channels:
        if isinstance(channel, discord.TextChannel):
            channels.append(ChannelInfo(id=channel.id, name=channel.name, type="text"))
        elif isinstance(channel, discord.VoiceChannel):
            channels.append(ChannelInfo(id=channel.id, name=channel.name, type="voice"))
        elif isinstance(channel, discord.CategoryChannel):
            channels.append(ChannelInfo(id=channel.id, name=channel.name, type="category"))

    # ロール一覧（@everyoneを除く）
    roles = [
        RoleInfo(id=role.id, name=role.name, color=role.color.value, position=role.position)
        for role in guild.roles
        if role.name != "@everyone"
    ]
    roles.sort(key=lambda r: r.position, reverse=True)

    # 設定を取得
    settings = await _get_guild_settings(db, guild.id)

    return GuildDetailResponse(
        info=GuildInfo(
            id=guild.id,
            name=guild.name,
            icon_url=str(guild.icon.url) if guild.icon else None,
            member_count=guild.member_count,
            bot_joined=True,
        ),
        channels=channels,
        roles=roles,
        settings=settings,
    )


async def _get_guild_settings(db: Database, guild_id: int) -> GuildSettings:
    """ギルドの全設定を取得"""
    # レベリング設定
    leveling_data = await db.get_leveling_settings(guild_id)
    leveling = LevelingSettings(
        enabled=bool(leveling_data.get("enabled", True)),
        ignored_channels=json.loads(leveling_data.get("ignored_channels", "[]")),
    )

    # スター設定
    star_data = await db.get_star_settings(guild_id)
    star = StarSettings(
        enabled=bool(star_data.get("enabled", True)),
        target_channels=json.loads(star_data.get("target_channels", "[]")),
        weekly_report_channel_id=star_data.get("weekly_report_channel_id"),
    )

    # 単語カウンター設定
    wc_data = await db.get_wordcounter_settings(guild_id)
    wordcounter = WordCounterSettings(
        enabled=bool(wc_data.get("enabled", True)) if wc_data else True,
        words=json.loads(wc_data.get("words", "[]")) if wc_data else [],
        milestones=json.loads(wc_data.get("milestones", "[10,50,100,200,300,500,1000]")) if wc_data else [10, 50, 100, 200, 300, 500, 1000],
    )

    # ロガー設定
    logger_data = await db.get_logger_settings(guild_id)
    logger_settings = LoggerSettings(
        enabled=bool(logger_data.get("enabled", False)) if logger_data else False,
        channel_id=logger_data.get("channel_id") if logger_data else None,
        log_messages=bool(logger_data.get("log_messages", True)) if logger_data else True,
        log_channels=bool(logger_data.get("log_channels", True)) if logger_data else True,
        log_roles=bool(logger_data.get("log_roles", True)) if logger_data else True,
        log_members=bool(logger_data.get("log_members", True)) if logger_data else True,
    )

    # 自動ロール設定
    autorole_data = await db.get_autorole_settings(guild_id)
    autorole = AutoroleSettings(
        enabled=bool(autorole_data.get("enabled", True)) if autorole_data else True,
        human_role_id=autorole_data.get("human_role_id") if autorole_data else None,
        bot_role_id=autorole_data.get("bot_role_id") if autorole_data else None,
    )

    # チケット設定
    ticket_data = await db.get_ticket_settings(guild_id)
    ticket = TicketSettings(
        category_id=ticket_data.get("category_id") if ticket_data else None,
        panel_channel_id=ticket_data.get("panel_channel_id") if ticket_data else None,
        panel_message_id=ticket_data.get("panel_message_id") if ticket_data else None,
        ticket_counter=ticket_data.get("ticket_counter", 0) if ticket_data else 0,
    )

    # 音楽設定
    music_data = await db.get_music_settings(guild_id)
    music = MusicSettings(
        default_volume=music_data.get("default_volume", 50) if music_data else 50,
        dj_role_id=music_data.get("dj_role_id") if music_data else None,
        music_channel_id=music_data.get("music_channel_id") if music_data else None,
    )

    return GuildSettings(
        leveling=leveling,
        star=star,
        wordcounter=wordcounter,
        logger=logger_settings,
        autorole=autorole,
        ticket=ticket,
        music=music,
    )


# ==================== 設定更新 ====================

@guilds_router.patch("/{guild_id}/settings/leveling", response_model=LevelingSettings)
async def update_leveling_settings(
    data: LevelingSettingsUpdate,
    guild: discord.Guild = Depends(require_guild_admin),
    db: Database = Depends(get_db),
) -> LevelingSettings:
    """レベリング設定を更新"""
    if data.enabled is not None:
        await db.set_leveling_enabled(guild.id, data.enabled)
    if data.ignored_channels is not None:
        await db.set_leveling_ignored_channels(guild.id, data.ignored_channels)

    settings = await db.get_leveling_settings(guild.id)
    return LevelingSettings(
        enabled=bool(settings.get("enabled", True)),
        ignored_channels=json.loads(settings.get("ignored_channels", "[]")),
    )


@guilds_router.patch("/{guild_id}/settings/star", response_model=StarSettings)
async def update_star_settings(
    data: StarSettingsUpdate,
    guild: discord.Guild = Depends(require_guild_admin),
    db: Database = Depends(get_db),
) -> StarSettings:
    """スター設定を更新"""
    if data.enabled is not None:
        await db.set_star_enabled(guild.id, data.enabled)
    if data.target_channels is not None:
        await db.set_star_target_channels(guild.id, data.target_channels)
    if data.weekly_report_channel_id is not None:
        await db.set_star_weekly_report_channel(guild.id, data.weekly_report_channel_id)

    settings = await db.get_star_settings(guild.id)
    return StarSettings(
        enabled=bool(settings.get("enabled", True)),
        target_channels=json.loads(settings.get("target_channels", "[]")),
        weekly_report_channel_id=settings.get("weekly_report_channel_id"),
    )


@guilds_router.patch("/{guild_id}/settings/wordcounter", response_model=WordCounterSettings)
async def update_wordcounter_settings(
    data: WordCounterSettingsUpdate,
    guild: discord.Guild = Depends(require_guild_admin),
    db: Database = Depends(get_db),
) -> WordCounterSettings:
    """単語カウンター設定を更新"""
    if data.enabled is not None:
        await db.set_wordcounter_enabled(guild.id, data.enabled)
    if data.words is not None:
        # 現在の単語をクリアして新しい単語を追加
        await db.clear_counter_words(guild.id)
        for word in data.words:
            await db.add_counter_word(guild.id, word)

    settings = await db.get_wordcounter_settings(guild.id)
    return WordCounterSettings(
        enabled=bool(settings.get("enabled", True)) if settings else True,
        words=json.loads(settings.get("words", "[]")) if settings else [],
        milestones=json.loads(settings.get("milestones", "[10,50,100,200,300,500,1000]")) if settings else [10, 50, 100, 200, 300, 500, 1000],
    )


@guilds_router.patch("/{guild_id}/settings/logger", response_model=LoggerSettings)
async def update_logger_settings(
    data: LoggerSettingsUpdate,
    guild: discord.Guild = Depends(require_guild_admin),
    db: Database = Depends(get_db),
) -> LoggerSettings:
    """ロガー設定を更新"""
    if data.enabled is not None:
        await db.set_logger_enabled(guild.id, data.enabled)
    if data.channel_id is not None:
        await db.set_logger_channel(guild.id, data.channel_id)

    settings = await db.get_logger_settings(guild.id)
    return LoggerSettings(
        enabled=bool(settings.get("enabled", False)) if settings else False,
        channel_id=settings.get("channel_id") if settings else None,
        log_messages=bool(settings.get("log_messages", True)) if settings else True,
        log_channels=bool(settings.get("log_channels", True)) if settings else True,
        log_roles=bool(settings.get("log_roles", True)) if settings else True,
        log_members=bool(settings.get("log_members", True)) if settings else True,
    )


@guilds_router.patch("/{guild_id}/settings/autorole", response_model=AutoroleSettings)
async def update_autorole_settings(
    data: AutoroleSettingsUpdate,
    guild: discord.Guild = Depends(require_guild_admin),
    db: Database = Depends(get_db),
) -> AutoroleSettings:
    """自動ロール設定を更新"""
    if data.enabled is not None:
        await db.set_autorole_enabled(guild.id, data.enabled)
    if data.human_role_id is not None:
        await db.set_autorole_human_role(guild.id, data.human_role_id)
    if data.bot_role_id is not None:
        await db.set_autorole_bot_role(guild.id, data.bot_role_id)

    settings = await db.get_autorole_settings(guild.id)
    return AutoroleSettings(
        enabled=bool(settings.get("enabled", True)) if settings else True,
        human_role_id=settings.get("human_role_id") if settings else None,
        bot_role_id=settings.get("bot_role_id") if settings else None,
    )


@guilds_router.patch("/{guild_id}/settings/music", response_model=MusicSettings)
async def update_music_settings(
    data: MusicSettingsUpdate,
    guild: discord.Guild = Depends(require_guild_admin),
    db: Database = Depends(get_db),
) -> MusicSettings:
    """音楽設定を更新"""
    if data.default_volume is not None:
        await db.set_music_volume(guild.id, data.default_volume)
    if data.dj_role_id is not None:
        await db.set_music_dj_role(guild.id, data.dj_role_id)
    if data.music_channel_id is not None:
        await db.set_music_channel(guild.id, data.music_channel_id)

    settings = await db.get_music_settings(guild.id)
    return MusicSettings(
        default_volume=settings.get("default_volume", 50) if settings else 50,
        dj_role_id=settings.get("dj_role_id") if settings else None,
        music_channel_id=settings.get("music_channel_id") if settings else None,
    )
