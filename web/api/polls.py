"""
Poll API エンドポイント
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import discord
from fastapi import APIRouter, Depends, HTTPException, status

from utils.database import Database
from utils.logging import get_logger
from web.auth.dependencies import get_bot, get_db, require_guild_admin
from web.schemas.poll import (
    PollCreate,
    PollListItem,
    PollListResponse,
    PollResponse,
    PollResultResponse,
    PollVoteResult,
)

if TYPE_CHECKING:
    from bot import SumireBot

logger = get_logger("sumire.web.api.polls")

polls_router = APIRouter()


def _calculate_vote_results(options: list[str], votes: dict[str, list[int]]) -> list[PollVoteResult]:
    """投票結果を計算"""
    # 各オプションの投票者リストを作成
    option_voters: dict[int, list[int]] = {i: [] for i in range(len(options))}

    for user_id_str, user_votes in votes.items():
        user_id = int(user_id_str)
        for option_idx in user_votes:
            if 0 <= option_idx < len(options):
                option_voters[option_idx].append(user_id)

    # 総投票数
    total_votes = sum(len(voters) for voters in option_voters.values())

    results = []
    for idx, option in enumerate(options):
        voters = option_voters[idx]
        count = len(voters)
        percentage = (count / total_votes * 100) if total_votes > 0 else 0.0

        results.append(PollVoteResult(
            option=option,
            count=count,
            percentage=percentage,
            voters=[str(v) for v in voters],  # Convert to strings
        ))

    return results


@polls_router.get("", response_model=PollListResponse)
async def list_polls(
    guild: discord.Guild = Depends(require_guild_admin),
    db: Database = Depends(get_db),
) -> PollListResponse:
    """ギルドのPoll一覧を取得"""
    polls = await db.get_guild_polls(guild.id)

    active = []
    ended = []

    for p in polls:
        # 総投票数を計算
        total_votes = 0
        for user_votes in p["votes"].values():
            total_votes += len(user_votes)

        end_time = None
        if p.get("end_time"):
            end_time = datetime.fromisoformat(p["end_time"])

        item = PollListItem(
            id=p["id"],
            channel_id=str(p["channel_id"]),  # Convert to string
            message_id=str(p["message_id"]),  # Convert to string
            question=p["question"],
            option_count=len(p["options"]),
            total_votes=total_votes,
            multi_select=bool(p["multi_select"]),
            end_time=end_time,
            ended=bool(p["ended"]),
            created_at=datetime.fromisoformat(p["created_at"]) if p.get("created_at") else datetime.utcnow(),
        )

        if p["ended"]:
            ended.append(item)
        else:
            active.append(item)

    return PollListResponse(
        active=active,
        ended=ended,
        total_active=len(active),
        total_ended=len(ended),
    )


@polls_router.get("/{poll_id}", response_model=PollResponse)
async def get_poll(
    poll_id: int,
    guild: discord.Guild = Depends(require_guild_admin),
    db: Database = Depends(get_db),
) -> PollResponse:
    """Poll詳細を取得"""
    poll = await db.get_poll_by_id(poll_id)

    if not poll or poll["guild_id"] != guild.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Poll not found"
        )

    end_time = None
    if poll.get("end_time"):
        end_time = datetime.fromisoformat(poll["end_time"])

    # votesの形式を変換（user_id -> [option_indices] から option -> [user_ids]へ）
    votes_by_option: dict[str, list[str]] = {}
    for option in poll["options"]:
        votes_by_option[option] = []

    for user_id_str, user_votes in poll["votes"].items():
        for option_idx in user_votes:
            if 0 <= option_idx < len(poll["options"]):
                option = poll["options"][option_idx]
                votes_by_option[option].append(user_id_str)  # Keep as string

    return PollResponse(
        id=poll["id"],
        guild_id=str(poll["guild_id"]),  # Convert to string
        channel_id=str(poll["channel_id"]),  # Convert to string
        message_id=str(poll["message_id"]),  # Convert to string
        author_id=str(poll["author_id"]),  # Convert to string
        question=poll["question"],
        options=poll["options"],
        votes=votes_by_option,
        multi_select=bool(poll["multi_select"]),
        end_time=end_time,
        ended=bool(poll["ended"]),
        created_at=datetime.fromisoformat(poll["created_at"]) if poll.get("created_at") else datetime.utcnow(),
    )


@polls_router.get("/{poll_id}/results", response_model=PollResultResponse)
async def get_poll_results(
    poll_id: int,
    guild: discord.Guild = Depends(require_guild_admin),
    db: Database = Depends(get_db),
) -> PollResultResponse:
    """Poll結果を取得"""
    poll = await db.get_poll_by_id(poll_id)

    if not poll or poll["guild_id"] != guild.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Poll not found"
        )

    results = _calculate_vote_results(poll["options"], poll["votes"])
    total_votes = sum(r.count for r in results)

    return PollResultResponse(
        id=poll["id"],
        question=poll["question"],
        results=results,
        total_votes=total_votes,
        ended=bool(poll["ended"]),
    )


@polls_router.post("", response_model=PollResponse, status_code=status.HTTP_201_CREATED)
async def create_poll(
    data: PollCreate,
    guild: discord.Guild = Depends(require_guild_admin),
    bot: "SumireBot" = Depends(get_bot),
    db: Database = Depends(get_db),
) -> PollResponse:
    """Pollを作成"""
    # チャンネルを取得 (string ID を int に変換)
    channel = guild.get_channel(int(data.channel_id))
    if not channel or not isinstance(channel, discord.TextChannel):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid channel or channel not found"
        )

    # Botが送信権限を持っているか確認
    permissions = channel.permissions_for(guild.me)
    if not permissions.send_messages or not permissions.view_channel:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bot does not have permission to send messages in this channel"
        )

    end_time = None
    if data.duration_seconds:
        end_time = datetime.utcnow() + timedelta(seconds=data.duration_seconds)

    # Viewをインポート（循環参照回避）
    from views.poll_views import PollView

    # Viewを作成
    poll_view = PollView(
        question=data.question,
        options=data.options,
        votes={},
        multi_select=data.multi_select,
        end_time=end_time,
    )

    # メッセージを送信
    try:
        message = await channel.send(view=poll_view)
    except discord.HTTPException as e:
        logger.error(f"Failed to send poll message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send poll message"
        )

    # データベースに保存
    poll_id = await db.create_poll(
        guild_id=guild.id,
        channel_id=channel.id,
        message_id=message.id,
        author_id=bot.user.id,
        question=data.question,
        options=data.options,
        multi_select=data.multi_select,
        end_time=end_time,
    )

    logger.info(f"Poll created via Web API: {data.question} in {guild.name}")

    # votesの形式を作成
    votes_by_option: dict[str, list[str]] = {option: [] for option in data.options}

    return PollResponse(
        id=poll_id,
        guild_id=str(guild.id),  # Convert to string
        channel_id=str(channel.id),  # Convert to string
        message_id=str(message.id),  # Convert to string
        author_id=str(bot.user.id),  # Convert to string
        question=data.question,
        options=data.options,
        votes=votes_by_option,
        multi_select=data.multi_select,
        end_time=end_time,
        ended=False,
        created_at=datetime.utcnow(),
    )


@polls_router.post("/{poll_id}/end", response_model=PollResultResponse)
async def end_poll(
    poll_id: int,
    guild: discord.Guild = Depends(require_guild_admin),
    bot: "SumireBot" = Depends(get_bot),
    db: Database = Depends(get_db),
) -> PollResultResponse:
    """Pollを終了"""
    poll = await db.get_poll_by_id(poll_id)

    if not poll or poll["guild_id"] != guild.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Poll not found"
        )

    if poll["ended"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Poll is already ended"
        )

    # データベースを更新
    await db.end_poll_by_id(poll_id)

    # Discordメッセージを更新
    channel = guild.get_channel(poll["channel_id"])
    if channel:
        try:
            message = await channel.fetch_message(poll["message_id"])

            # Viewをインポート
            from views.poll_views import PollEndedView

            new_view = PollEndedView(
                question=poll["question"],
                options=poll["options"],
                votes=poll["votes"],
            )

            await message.edit(view=new_view)

        except discord.HTTPException as e:
            logger.error(f"Failed to update poll message: {e}")

    logger.info(f"Poll ended via Web API: {poll['question']}")

    results = _calculate_vote_results(poll["options"], poll["votes"])
    total_votes = sum(r.count for r in results)

    return PollResultResponse(
        id=poll_id,
        question=poll["question"],
        results=results,
        total_votes=total_votes,
        ended=True,
    )
