"""
Giveaway Cog
抽選機能を提供
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import discord
from discord import app_commands, ui
from discord.ext import commands, tasks

from utils.config import Config
from utils.database import Database
from utils.logging import get_logger
from utils.time_parser import parse_duration, format_duration
from utils.checks import Checks
from views.giveaway_views import GiveawayView, GiveawayEndedView, GiveawayNoParticipantsView
from views.common_views import CommonErrorView, CommonSuccessView, CommonWarningView

if TYPE_CHECKING:
    from bot import SumireBot

logger = get_logger("sumire.cogs.giveaway")


class Giveaway(commands.Cog):
    """Giveaway（抽選）機能"""

    def __init__(self, bot: SumireBot) -> None:
        self.bot = bot
        self.db = Database()
        self.config = Config()

    async def cog_load(self) -> None:
        """Cog読み込み時"""
        # 永続的Viewを登録
        self.bot.add_view(GiveawayView(
            prize="placeholder",
            host=self.bot.user,
            end_time=datetime.utcnow(),
            participant_count=0
        ))
        # チェックタスクを開始
        self.check_ended_giveaways.start()
        logger.info("Giveaway Cog loaded")

    async def cog_unload(self) -> None:
        """Cog解除時"""
        self.check_ended_giveaways.cancel()

    @tasks.loop(seconds=30)
    async def check_ended_giveaways(self) -> None:
        """終了時刻を過ぎたGiveawayをチェック"""
        try:
            giveaways = await self.db.get_active_giveaways()
            now = datetime.utcnow()

            for giveaway in giveaways:
                end_time = datetime.fromisoformat(giveaway["end_time"])
                if now >= end_time:
                    await self._end_giveaway(giveaway)
        except Exception as e:
            logger.error(f"Giveawayチェックエラー: {e}")

    @check_ended_giveaways.before_loop
    async def before_check(self) -> None:
        """チェックタスク開始前にBotの準備を待つ"""
        await self.bot.wait_until_ready()

    async def _end_giveaway(self, giveaway: dict) -> None:
        """Giveawayを終了して当選者を発表"""
        try:
            channel = self.bot.get_channel(giveaway["channel_id"])
            if not channel:
                logger.warning(f"Giveawayチャンネルが見つかりません: {giveaway['channel_id']}")
                await self.db.end_giveaway(giveaway["message_id"], [])
                return

            try:
                message = await channel.fetch_message(giveaway["message_id"])
            except discord.NotFound:
                logger.warning(f"Giveawayメッセージが見つかりません: {giveaway['message_id']}")
                await self.db.end_giveaway(giveaway["message_id"], [])
                return

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
            await self.db.end_giveaway(giveaway["message_id"], winners_ids)

            # 当選者のユーザーオブジェクトを取得
            winners = []
            guild = channel.guild
            for winner_id in winners_ids:
                member = guild.get_member(winner_id)
                if member:
                    winners.append(member)
                else:
                    try:
                        user = await self.bot.fetch_user(winner_id)
                        winners.append(user)
                    except Exception:
                        pass

            # 主催者を取得
            host = guild.get_member(giveaway["host_id"])
            if not host:
                try:
                    host = await self.bot.fetch_user(giveaway["host_id"])
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
                    f"「**{giveaway['prize']}**」に当選しました！"
                )

            logger.info(f"Giveaway終了: {giveaway['prize']} - 当選者: {len(winners)}人")

        except Exception as e:
            logger.error(f"Giveaway終了処理エラー: {e}", exc_info=True)

    @app_commands.command(name="giveaway", description="Giveaway（抽選）を開始します")
    @app_commands.describe(
        prize="賞品名",
        duration="期間（例: 1d, 12h, 30m, 1d12h）",
        winners="当選者数（デフォルト: 1）"
    )
    @app_commands.default_permissions(manage_guild=True)
    @Checks.is_mod()
    async def giveaway_start(
        self,
        interaction: discord.Interaction,
        prize: str,
        duration: str,
        winners: int = 1
    ) -> None:
        """Giveawayを開始"""
        # 期間をパース
        seconds = parse_duration(duration)
        if not seconds:
            view = CommonErrorView(
                title="無効な期間",
                description="期間の形式が正しくありません。\n"
                           "例: `1d`（1日）, `12h`（12時間）, `30m`（30分）, `1d12h`（1日12時間）"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # 最小1分、最大4週間
        if seconds < 60:
            view = CommonErrorView(
                title="期間が短すぎます",
                description="最小期間は1分です。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        if seconds > 2419200:  # 4週間
            view = CommonErrorView(
                title="期間が長すぎます",
                description="最大期間は4週間です。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # 当選者数チェック
        if winners < 1:
            winners = 1
        if winners > 20:
            view = CommonErrorView(
                title="当選者数が多すぎます",
                description="最大当選者数は20人です。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        end_time = datetime.utcnow() + timedelta(seconds=seconds)

        # Viewを作成
        giveaway_view = GiveawayView(
            prize=prize,
            host=interaction.user,
            end_time=end_time,
            participant_count=0,
            winner_count=winners
        )

        # メッセージを送信
        await interaction.response.send_message(view=giveaway_view)
        message = await interaction.original_response()

        # データベースに保存
        await self.db.create_giveaway(
            guild_id=interaction.guild.id,
            channel_id=interaction.channel.id,
            message_id=message.id,
            host_id=interaction.user.id,
            prize=prize,
            winner_count=winners,
            end_time=end_time
        )

        logger.info(
            f"Giveaway開始: {prize} by {interaction.user} "
            f"(終了: {format_duration(seconds)}, 当選者数: {winners})"
        )

    @app_commands.command(name="giveaway-end", description="Giveawayを早期終了します")
    @app_commands.describe(message_id="GiveawayメッセージのID")
    @app_commands.default_permissions(manage_guild=True)
    @Checks.is_mod()
    async def giveaway_end(
        self,
        interaction: discord.Interaction,
        message_id: str
    ) -> None:
        """Giveawayを早期終了"""
        try:
            msg_id = int(message_id)
        except ValueError:
            view = CommonErrorView(
                title="無効なID",
                description="メッセージIDが正しくありません。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        giveaway = await self.db.get_giveaway(msg_id)
        if not giveaway:
            view = CommonErrorView(
                title="見つかりません",
                description="指定されたGiveawayが見つかりません。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        if giveaway["ended"]:
            view = CommonWarningView(
                title="既に終了済み",
                description="このGiveawayは既に終了しています。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # 終了処理
        await self._end_giveaway(giveaway)

        view = CommonSuccessView(
            title="Giveaway終了",
            description=f"「{giveaway['prize']}」のGiveawayを終了しました。"
        )
        await interaction.followup.send(view=view, ephemeral=True)

    @app_commands.command(name="giveaway-reroll", description="Giveawayの当選者を再抽選します")
    @app_commands.describe(
        message_id="GiveawayメッセージのID",
        count="再抽選する人数（デフォルト: 1）"
    )
    @app_commands.default_permissions(manage_guild=True)
    @Checks.is_mod()
    async def giveaway_reroll(
        self,
        interaction: discord.Interaction,
        message_id: str,
        count: int = 1
    ) -> None:
        """Giveawayの当選者を再抽選"""
        try:
            msg_id = int(message_id)
        except ValueError:
            view = CommonErrorView(
                title="無効なID",
                description="メッセージIDが正しくありません。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        giveaway = await self.db.get_giveaway(msg_id)
        if not giveaway:
            view = CommonErrorView(
                title="見つかりません",
                description="指定されたGiveawayが見つかりません。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        if not giveaway["ended"]:
            view = CommonWarningView(
                title="まだ終了していません",
                description="Giveawayが終了してから再抽選してください。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        participants = giveaway["participants"]
        if not participants:
            view = CommonErrorView(
                title="参加者なし",
                description="参加者がいないため再抽選できません。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # 再抽選
        new_winners_ids = random.sample(
            participants,
            min(count, len(participants))
        )

        # 当選者のユーザーオブジェクトを取得
        new_winners = []
        for winner_id in new_winners_ids:
            member = interaction.guild.get_member(winner_id)
            if member:
                new_winners.append(member)
            else:
                try:
                    user = await self.bot.fetch_user(winner_id)
                    new_winners.append(user)
                except Exception:
                    pass

        if not new_winners:
            view = CommonErrorView(
                title="エラー",
                description="当選者を取得できませんでした。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # 新当選者を発表
        winner_mentions = " ".join(w.mention for w in new_winners)
        await interaction.response.send_message(
            f"🎊 **再抽選！** {winner_mentions}\n"
            f"「**{giveaway['prize']}**」に当選しました！"
        )

        logger.info(f"Giveaway再抽選: {giveaway['prize']} - 新当選者: {len(new_winners)}人")


async def setup(bot: SumireBot) -> None:
    """Cogをセットアップ"""
    await bot.add_cog(Giveaway(bot))
