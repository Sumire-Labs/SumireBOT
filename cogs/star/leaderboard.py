"""
Star ランキングコマンド
"""
from __future__ import annotations

from datetime import datetime, timedelta

import discord
from discord import app_commands

from utils.logging import get_logger
from views.common_views import CommonErrorView, CommonInfoView
from views.star_views import StarLeaderboardView

logger = get_logger("sumire.cogs.star.leaderboard")


class StarLeaderboardMixin:
    """Star ランキングコマンド Mixin"""

    @app_commands.command(name="starboard", description="スターランキングを表示します")
    @app_commands.describe(period="集計期間（weekly/monthly/all）")
    @app_commands.choices(period=[
        app_commands.Choice(name="週間", value="weekly"),
        app_commands.Choice(name="月間", value="monthly"),
        app_commands.Choice(name="全期間", value="all"),
    ])
    async def starboard(
        self,
        interaction: discord.Interaction,
        period: str = "weekly"
    ) -> None:
        """スターランキングを表示"""
        if not interaction.guild:
            view = CommonErrorView(
                title="エラー",
                description="このコマンドはサーバー内でのみ使用できます。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # 期間に応じたsince日時を計算
        since = None
        if period == "weekly":
            since = datetime.utcnow() - timedelta(days=7)
        elif period == "monthly":
            since = datetime.utcnow() - timedelta(days=30)
        # all の場合は None

        # ランキングを取得
        message_rankings = await self.db.get_star_leaderboard(
            interaction.guild.id,
            limit=10,
            since=since
        )
        author_rankings = await self.db.get_author_star_totals(
            interaction.guild.id,
            limit=10,
            since=since
        )

        # データがない場合
        if not message_rankings and not author_rankings:
            view = CommonInfoView(
                title="スターボード",
                description="まだスターデータがありません。\n対象チャンネルに投稿してスターをもらいましょう！"
            )
            await interaction.response.send_message(
                view=view,
                allowed_mentions=discord.AllowedMentions.none()
            )
            return

        view = StarLeaderboardView(
            guild=interaction.guild,
            message_rankings=message_rankings,
            author_rankings=author_rankings,
            period=period
        )

        await interaction.response.send_message(
            view=view,
            allowed_mentions=discord.AllowedMentions.none()
        )
