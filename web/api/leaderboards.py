"""
ランキングAPI エンドポイント
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional

import discord
from fastapi import APIRouter, Depends, Query

from utils.database import Database
from utils.logging import get_logger
from web.auth.dependencies import get_bot, get_db, require_guild_admin
from web.schemas.leaderboard import (
    LevelLeaderboardResponse,
    LevelRankEntry,
    ReactionLeaderboardResponse,
    ReactionRankEntry,
    StarLeaderboardResponse,
    StarMessageRankEntry,
    StarUserRankEntry,
    VCLeaderboardResponse,
    VCRankEntry,
    WordCountRankEntry,
    WordLeaderboardResponse,
    WordListResponse,
)

if TYPE_CHECKING:
    from bot import SumireBot

logger = get_logger("sumire.web.api.leaderboards")

leaderboards_router = APIRouter()


def _get_user_info(bot: "SumireBot", guild: discord.Guild, user_id: int) -> tuple[str, str, Optional[str]]:
    """ユーザー情報を取得"""
    member = guild.get_member(user_id)
    if member:
        return (
            member.name,
            member.display_name,
            str(member.display_avatar.url) if member.display_avatar else None,
        )
    # メンバーが見つからない場合
    return (f"User {user_id}", f"User {user_id}", None)


# ==================== レベルランキング ====================

@leaderboards_router.get("/levels", response_model=LevelLeaderboardResponse)
async def get_level_leaderboard(
    guild: discord.Guild = Depends(require_guild_admin),
    bot: "SumireBot" = Depends(get_bot),
    db: Database = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> LevelLeaderboardResponse:
    """レベルランキングを取得"""
    rankings = await db.get_level_leaderboard(guild.id, limit=limit, offset=offset)
    total = await db.get_level_user_count(guild.id)

    entries = []
    for i, row in enumerate(rankings):
        username, display_name, avatar_url = _get_user_info(bot, guild, row["user_id"])
        entries.append(LevelRankEntry(
            rank=offset + i + 1,
            user_id=row["user_id"],
            username=username,
            display_name=display_name,
            avatar_url=avatar_url,
            level=row["level"],
            xp=row["xp"],
            total_xp=row["xp"],  # 累計XPが別カラムなら調整
        ))

    return LevelLeaderboardResponse(entries=entries, total_users=total)


# ==================== VCランキング ====================

@leaderboards_router.get("/vc", response_model=VCLeaderboardResponse)
async def get_vc_leaderboard(
    guild: discord.Guild = Depends(require_guild_admin),
    bot: "SumireBot" = Depends(get_bot),
    db: Database = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> VCLeaderboardResponse:
    """VC時間ランキングを取得"""
    rankings = await db.get_vc_leaderboard(guild.id, limit=limit, offset=offset)
    total = await db.get_level_user_count(guild.id)

    entries = []
    for i, row in enumerate(rankings):
        username, display_name, avatar_url = _get_user_info(bot, guild, row["user_id"])
        entries.append(VCRankEntry(
            rank=offset + i + 1,
            user_id=row["user_id"],
            username=username,
            display_name=display_name,
            avatar_url=avatar_url,
            vc_time=row["vc_time"],
            vc_level=row["vc_level"],
        ))

    return VCLeaderboardResponse(entries=entries, total_users=total)


# ==================== スターランキング ====================

@leaderboards_router.get("/stars", response_model=StarLeaderboardResponse)
async def get_star_leaderboard(
    guild: discord.Guild = Depends(require_guild_admin),
    bot: "SumireBot" = Depends(get_bot),
    db: Database = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
) -> StarLeaderboardResponse:
    """スターランキングを取得"""
    # ユーザー別ランキング
    user_rankings = await db.get_star_user_leaderboard(guild.id, limit=limit)
    by_user = []
    for i, row in enumerate(user_rankings):
        username, display_name, avatar_url = _get_user_info(bot, guild, row["author_id"])
        by_user.append(StarUserRankEntry(
            rank=i + 1,
            user_id=row["author_id"],
            username=username,
            display_name=display_name,
            avatar_url=avatar_url,
            star_count=row["total_stars"],
            message_count=row["message_count"],
        ))

    # メッセージ別ランキング
    message_rankings = await db.get_star_message_leaderboard(guild.id, limit=limit)
    by_message = []
    for i, row in enumerate(message_rankings):
        username, _, _ = _get_user_info(bot, guild, row["author_id"])
        by_message.append(StarMessageRankEntry(
            rank=i + 1,
            message_id=row["message_id"],
            channel_id=row["channel_id"],
            author_id=row["author_id"],
            author_name=username,
            star_count=row["star_count"],
        ))

    total_users = len(user_rankings)
    total_messages = await db.get_star_message_count(guild.id)

    return StarLeaderboardResponse(
        by_user=by_user,
        by_message=by_message,
        total_users=total_users,
        total_messages=total_messages,
    )


# ==================== 単語カウンターランキング ====================

@leaderboards_router.get("/words", response_model=WordListResponse)
async def get_tracked_words(
    guild: discord.Guild = Depends(require_guild_admin),
    db: Database = Depends(get_db),
) -> WordListResponse:
    """追跡中の単語一覧を取得"""
    settings = await db.get_wordcounter_settings(guild.id)
    words = json.loads(settings.get("words", "[]")) if settings else []
    return WordListResponse(words=words)


@leaderboards_router.get("/words/{word}", response_model=WordLeaderboardResponse)
async def get_word_leaderboard(
    word: str,
    guild: discord.Guild = Depends(require_guild_admin),
    bot: "SumireBot" = Depends(get_bot),
    db: Database = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
) -> WordLeaderboardResponse:
    """単語別ランキングを取得"""
    rankings = await db.get_word_leaderboard(guild.id, word, limit=limit)

    entries = []
    for i, row in enumerate(rankings):
        username, display_name, avatar_url = _get_user_info(bot, guild, row["user_id"])
        entries.append(WordCountRankEntry(
            rank=i + 1,
            user_id=row["user_id"],
            username=username,
            display_name=display_name,
            avatar_url=avatar_url,
            word=word,
            count=row["count"],
        ))

    return WordLeaderboardResponse(
        word=word,
        entries=entries,
        total_users=len(entries),
    )


# ==================== リアクションランキング ====================

@leaderboards_router.get("/reactions", response_model=ReactionLeaderboardResponse)
async def get_reaction_leaderboard(
    guild: discord.Guild = Depends(require_guild_admin),
    bot: "SumireBot" = Depends(get_bot),
    db: Database = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
) -> ReactionLeaderboardResponse:
    """リアクションランキングを取得"""
    # 与えた数ランキング
    given_rankings = await db.get_reaction_given_leaderboard(guild.id, limit=limit)
    by_given = []
    for i, row in enumerate(given_rankings):
        username, display_name, avatar_url = _get_user_info(bot, guild, row["user_id"])
        by_given.append(ReactionRankEntry(
            rank=i + 1,
            user_id=row["user_id"],
            username=username,
            display_name=display_name,
            avatar_url=avatar_url,
            reactions_given=row["reactions_given"],
            reactions_received=row.get("reactions_received", 0),
        ))

    # もらった数ランキング
    received_rankings = await db.get_reaction_received_leaderboard(guild.id, limit=limit)
    by_received = []
    for i, row in enumerate(received_rankings):
        username, display_name, avatar_url = _get_user_info(bot, guild, row["user_id"])
        by_received.append(ReactionRankEntry(
            rank=i + 1,
            user_id=row["user_id"],
            username=username,
            display_name=display_name,
            avatar_url=avatar_url,
            reactions_given=row.get("reactions_given", 0),
            reactions_received=row["reactions_received"],
        ))

    total = await db.get_level_user_count(guild.id)

    return ReactionLeaderboardResponse(
        by_given=by_given,
        by_received=by_received,
        total_users=total,
    )
