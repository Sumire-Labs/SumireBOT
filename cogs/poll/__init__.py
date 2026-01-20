"""
Poll Cog
投票機能を提供
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

import discord
from discord import app_commands, ui
from discord.ext import commands, tasks

from utils.config import Config
from utils.database import Database
from utils.logging import get_logger
from utils.time_parser import parse_duration, format_duration
from views.poll_views import PollView, PollEndedView
from views.common_views import CommonErrorView, CommonSuccessView, CommonWarningView

if TYPE_CHECKING:
    from bot import SumireBot

logger = get_logger("sumire.cogs.poll")


class Poll(commands.Cog):
    """投票機能"""

    def __init__(self, bot: SumireBot) -> None:
        self.bot = bot
        self.db = Database()
        self.config = Config()

    async def cog_load(self) -> None:
        """Cog読み込み時"""
        # 永続的Viewを登録
        self.bot.add_view(PollView(
            question="placeholder",
            options=["1", "2"],
            votes={}
        ))
        # チェックタスクを開始
        self.check_ended_polls.start()
        logger.info("Poll Cog loaded")

    async def cog_unload(self) -> None:
        """Cog解除時"""
        self.check_ended_polls.cancel()

    @tasks.loop(seconds=30)
    async def check_ended_polls(self) -> None:
        """終了時刻を過ぎた投票をチェック"""
        try:
            polls = await self.db.get_active_polls()
            now = datetime.utcnow()

            for poll in polls:
                if poll.get("end_time"):
                    end_time = datetime.fromisoformat(poll["end_time"])
                    if now >= end_time:
                        await self._end_poll(poll)
        except Exception as e:
            logger.error(f"投票チェックエラー: {e}")

    @check_ended_polls.before_loop
    async def before_check(self) -> None:
        """チェックタスク開始前にBotの準備を待つ"""
        await self.bot.wait_until_ready()

    async def _end_poll(self, poll: dict) -> None:
        """投票を終了"""
        try:
            channel = self.bot.get_channel(poll["channel_id"])
            if not channel:
                logger.warning(f"投票チャンネルが見つかりません: {poll['channel_id']}")
                await self.db.end_poll(poll["message_id"])
                return

            try:
                message = await channel.fetch_message(poll["message_id"])
            except discord.NotFound:
                logger.warning(f"投票メッセージが見つかりません: {poll['message_id']}")
                await self.db.end_poll(poll["message_id"])
                return

            # データベースを更新
            await self.db.end_poll(poll["message_id"])

            # Viewを更新
            new_view = PollEndedView(
                question=poll["question"],
                options=poll["options"],
                votes=poll["votes"]
            )

            await message.edit(view=new_view)
            logger.info(f"投票終了: {poll['question']}")

        except Exception as e:
            logger.error(f"投票終了処理エラー: {e}", exc_info=True)

    @app_commands.command(name="poll", description="投票を作成します")
    @app_commands.describe(
        question="質問内容",
        option1="選択肢1",
        option2="選択肢2",
        option3="選択肢3（任意）",
        option4="選択肢4（任意）",
        option5="選択肢5（任意）",
        option6="選択肢6（任意）",
        option7="選択肢7（任意）",
        option8="選択肢8（任意）",
        option9="選択肢9（任意）",
        option10="選択肢10（任意）",
        multi_select="複数選択を許可（デフォルト: 不可）",
        duration="期間（例: 1d, 12h, 30m）空欄で無期限"
    )
    async def poll_create(
        self,
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: Optional[str] = None,
        option4: Optional[str] = None,
        option5: Optional[str] = None,
        option6: Optional[str] = None,
        option7: Optional[str] = None,
        option8: Optional[str] = None,
        option9: Optional[str] = None,
        option10: Optional[str] = None,
        multi_select: bool = False,
        duration: Optional[str] = None
    ) -> None:
        """投票を作成"""
        # 選択肢をリストに
        options = [option1, option2]
        for opt in [option3, option4, option5, option6, option7, option8, option9, option10]:
            if opt:
                options.append(opt)

        # 期間をパース
        end_time = None
        if duration:
            seconds = parse_duration(duration)
            if not seconds:
                view = CommonErrorView(
                    title="無効な期間",
                    description="期間の形式が正しくありません。\n"
                               "例: `1d`（1日）, `12h`（12時間）, `30m`（30分）"
                )
                await interaction.response.send_message(view=view, ephemeral=True)
                return

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

            end_time = datetime.utcnow() + timedelta(seconds=seconds)

        # Viewを作成
        poll_view = PollView(
            question=question,
            options=options,
            votes={},
            multi_select=multi_select,
            end_time=end_time
        )

        # メッセージを送信
        await interaction.response.send_message(view=poll_view)
        message = await interaction.original_response()

        # データベースに保存
        await self.db.create_poll(
            guild_id=interaction.guild.id,
            channel_id=interaction.channel.id,
            message_id=message.id,
            author_id=interaction.user.id,
            question=question,
            options=options,
            multi_select=multi_select,
            end_time=end_time
        )

        duration_text = format_duration(seconds) if duration and seconds else "無期限"
        logger.info(
            f"投票作成: {question} by {interaction.user} "
            f"(選択肢: {len(options)}, 複数選択: {multi_select}, 期間: {duration_text})"
        )

    @app_commands.command(name="poll-end", description="投票を終了します")
    @app_commands.describe(message_id="投票メッセージのID")
    async def poll_end(
        self,
        interaction: discord.Interaction,
        message_id: str
    ) -> None:
        """投票を終了"""
        try:
            msg_id = int(message_id)
        except ValueError:
            view = CommonErrorView(
                title="無効なID",
                description="メッセージIDが正しくありません。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        poll = await self.db.get_poll(msg_id)
        if not poll:
            view = CommonErrorView(
                title="見つかりません",
                description="指定された投票が見つかりません。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # 作成者または管理者のみ終了可能
        is_author = poll["author_id"] == interaction.user.id
        is_admin = interaction.user.guild_permissions.manage_guild
        if not is_author and not is_admin:
            view = CommonErrorView(
                title="権限エラー",
                description="投票を終了できるのは作成者または管理者のみです。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        if poll["ended"]:
            view = CommonWarningView(
                title="既に終了済み",
                description="この投票は既に終了しています。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # 終了処理
        await self._end_poll(poll)

        view = CommonSuccessView(
            title="投票終了",
            description=f"投票「{poll['question']}」を終了しました。"
        )
        await interaction.followup.send(view=view, ephemeral=True)


async def setup(bot: SumireBot) -> None:
    """Cogをセットアップ"""
    await bot.add_cog(Poll(bot))
