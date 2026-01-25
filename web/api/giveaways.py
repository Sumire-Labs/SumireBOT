"""
Giveaway API エンドポイント
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import discord
from fastapi import APIRouter, Depends, HTTPException, status

from utils.database import Database
from utils.logging import get_logger
from web.auth.dependencies import get_bot, get_db, require_guild_admin
from web.schemas.giveaway import (
    GiveawayCreate,
    GiveawayEndResponse,
    GiveawayListItem,
    GiveawayListResponse,
    GiveawayRerollResponse,
    GiveawayResponse,
)

if TYPE_CHECKING:
    from bot import SumireBot

logger = get_logger("sumire.web.api.giveaways")

giveaways_router = APIRouter()


@giveaways_router.get("", response_model=GiveawayListResponse)
async def list_giveaways(
    guild: discord.Guild = Depends(require_guild_admin),
    db: Database = Depends(get_db),
) -> GiveawayListResponse:
    """ギルドのGiveaway一覧を取得"""
    giveaways = await db.get_guild_giveaways(guild.id)

    active = []
    ended = []

    for g in giveaways:
        item = GiveawayListItem(
            id=g["id"],
            channel_id=g["channel_id"],
            message_id=g["message_id"],
            prize=g["prize"],
            winner_count=g["winner_count"],
            participant_count=len(g["participants"]),
            end_time=datetime.fromisoformat(g["end_time"]),
            ended=bool(g["ended"]),
            created_at=datetime.fromisoformat(g["created_at"]) if g.get("created_at") else datetime.utcnow(),
        )

        if g["ended"]:
            ended.append(item)
        else:
            active.append(item)

    return GiveawayListResponse(
        active=active,
        ended=ended,
        total_active=len(active),
        total_ended=len(ended),
    )


@giveaways_router.get("/{giveaway_id}", response_model=GiveawayResponse)
async def get_giveaway(
    giveaway_id: int,
    guild: discord.Guild = Depends(require_guild_admin),
    db: Database = Depends(get_db),
) -> GiveawayResponse:
    """Giveaway詳細を取得"""
    giveaway = await db.get_giveaway_by_id(giveaway_id)

    if not giveaway or giveaway["guild_id"] != guild.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Giveaway not found"
        )

    return GiveawayResponse(
        id=giveaway["id"],
        guild_id=giveaway["guild_id"],
        channel_id=giveaway["channel_id"],
        message_id=giveaway["message_id"],
        host_id=giveaway["host_id"],
        prize=giveaway["prize"],
        winner_count=giveaway["winner_count"],
        end_time=datetime.fromisoformat(giveaway["end_time"]),
        participants=giveaway["participants"],
        winners=giveaway["winners"],
        ended=bool(giveaway["ended"]),
        created_at=datetime.fromisoformat(giveaway["created_at"]) if giveaway.get("created_at") else datetime.utcnow(),
    )


@giveaways_router.post("", response_model=GiveawayResponse, status_code=status.HTTP_201_CREATED)
async def create_giveaway(
    data: GiveawayCreate,
    guild: discord.Guild = Depends(require_guild_admin),
    bot: "SumireBot" = Depends(get_bot),
    db: Database = Depends(get_db),
) -> GiveawayResponse:
    """Giveawayを作成"""
    # チャンネルを取得
    channel = guild.get_channel(data.channel_id)
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

    end_time = datetime.utcnow() + timedelta(seconds=data.duration_seconds)

    # Viewをインポート（循環参照回避）
    from views.giveaway_views import GiveawayView

    # Viewを作成
    giveaway_view = GiveawayView(
        prize=data.prize,
        host=bot.user,
        end_time=end_time,
        participant_count=0,
        winner_count=data.winner_count
    )

    # メッセージを送信
    try:
        message = await channel.send(view=giveaway_view)
    except discord.HTTPException as e:
        logger.error(f"Failed to send giveaway message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send giveaway message"
        )

    # データベースに保存
    giveaway_id = await db.create_giveaway(
        guild_id=guild.id,
        channel_id=channel.id,
        message_id=message.id,
        host_id=bot.user.id,
        prize=data.prize,
        winner_count=data.winner_count,
        end_time=end_time
    )

    logger.info(f"Giveaway created via Web API: {data.prize} in {guild.name}")

    return GiveawayResponse(
        id=giveaway_id,
        guild_id=guild.id,
        channel_id=channel.id,
        message_id=message.id,
        host_id=bot.user.id,
        prize=data.prize,
        winner_count=data.winner_count,
        end_time=end_time,
        participants=[],
        winners=[],
        ended=False,
        created_at=datetime.utcnow(),
    )


@giveaways_router.post("/{giveaway_id}/end", response_model=GiveawayEndResponse)
async def end_giveaway(
    giveaway_id: int,
    guild: discord.Guild = Depends(require_guild_admin),
    bot: "SumireBot" = Depends(get_bot),
    db: Database = Depends(get_db),
) -> GiveawayEndResponse:
    """Giveawayを終了"""
    giveaway = await db.get_giveaway_by_id(giveaway_id)

    if not giveaway or giveaway["guild_id"] != guild.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Giveaway not found"
        )

    if giveaway["ended"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Giveaway is already ended"
        )

    participants = giveaway["participants"]
    winner_count = giveaway["winner_count"]

    # 当選者を抽選
    if participants:
        winners_ids = random.sample(
            participants,
            min(winner_count, len(participants))
        )
    else:
        winners_ids = []

    # データベースを更新
    await db.end_giveaway_by_id(giveaway_id, winners_ids)

    # 当選者の名前を取得
    winner_names = []
    for winner_id in winners_ids:
        member = guild.get_member(winner_id)
        if member:
            winner_names.append(member.display_name)
        else:
            try:
                user = await bot.fetch_user(winner_id)
                winner_names.append(user.name)
            except Exception:
                winner_names.append(f"User#{winner_id}")

    # Discordメッセージを更新
    channel = guild.get_channel(giveaway["channel_id"])
    if channel:
        try:
            message = await channel.fetch_message(giveaway["message_id"])

            # Viewをインポート
            from views.giveaway_views import GiveawayEndedView, GiveawayNoParticipantsView

            # 当選者のユーザーオブジェクトを取得
            winners = []
            for winner_id in winners_ids:
                member = guild.get_member(winner_id)
                if member:
                    winners.append(member)
                else:
                    try:
                        user = await bot.fetch_user(winner_id)
                        winners.append(user)
                    except Exception:
                        pass

            # 主催者を取得
            host = guild.get_member(giveaway["host_id"])
            if not host:
                try:
                    host = await bot.fetch_user(giveaway["host_id"])
                except Exception:
                    host = None

            # Viewを更新
            if winners:
                new_view = GiveawayEndedView(
                    prize=giveaway["prize"],
                    winners=winners,
                    participant_count=len(participants),
                    host=host
                )
            else:
                new_view = GiveawayNoParticipantsView(prize=giveaway["prize"])

            await message.edit(view=new_view)

            # 当選者をメンション
            if winners:
                winner_mentions = " ".join(w.mention for w in winners)
                await channel.send(
                    f"🎊 **おめでとうございます！** {winner_mentions}\n"
                    f"「**{giveaway['prize']}**」に当選しました！",
                    allowed_mentions=discord.AllowedMentions.none()
                )

        except discord.HTTPException as e:
            logger.error(f"Failed to update giveaway message: {e}")

    logger.info(f"Giveaway ended via Web API: {giveaway['prize']} - Winners: {len(winners_ids)}")

    return GiveawayEndResponse(
        id=giveaway_id,
        prize=giveaway["prize"],
        winners=winners_ids,
        winner_names=winner_names,
    )


@giveaways_router.post("/{giveaway_id}/reroll", response_model=GiveawayRerollResponse)
async def reroll_giveaway(
    giveaway_id: int,
    count: int = 1,
    guild: discord.Guild = Depends(require_guild_admin),
    bot: "SumireBot" = Depends(get_bot),
    db: Database = Depends(get_db),
) -> GiveawayRerollResponse:
    """Giveawayの当選者を再抽選"""
    giveaway = await db.get_giveaway_by_id(giveaway_id)

    if not giveaway or giveaway["guild_id"] != guild.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Giveaway not found"
        )

    if not giveaway["ended"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Giveaway is not ended yet"
        )

    participants = giveaway["participants"]
    if not participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No participants to reroll"
        )

    # 再抽選
    new_winners_ids = random.sample(
        participants,
        min(count, len(participants))
    )

    # 当選者リストを更新
    await db.update_giveaway_winners(giveaway_id, new_winners_ids)

    # 当選者の名前を取得
    new_winner_names = []
    new_winners = []
    for winner_id in new_winners_ids:
        member = guild.get_member(winner_id)
        if member:
            new_winners.append(member)
            new_winner_names.append(member.display_name)
        else:
            try:
                user = await bot.fetch_user(winner_id)
                new_winners.append(user)
                new_winner_names.append(user.name)
            except Exception:
                new_winner_names.append(f"User#{winner_id}")

    # Discordに新当選者を発表
    channel = guild.get_channel(giveaway["channel_id"])
    if channel and new_winners:
        try:
            winner_mentions = " ".join(w.mention for w in new_winners)
            await channel.send(
                f"🎊 **再抽選！** {winner_mentions}\n"
                f"「**{giveaway['prize']}**」に当選しました！",
                allowed_mentions=discord.AllowedMentions.none()
            )
        except discord.HTTPException as e:
            logger.error(f"Failed to send reroll message: {e}")

    logger.info(f"Giveaway rerolled via Web API: {giveaway['prize']} - New winners: {len(new_winners_ids)}")

    return GiveawayRerollResponse(
        id=giveaway_id,
        prize=giveaway["prize"],
        new_winners=new_winners_ids,
        new_winner_names=new_winner_names,
    )
