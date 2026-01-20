"""
Confess コマンド - 匿名メッセージ
"""
from __future__ import annotations

import discord
from discord import app_commands

from utils.logging import get_logger
from views.confess_views import ConfessView
from views.common_views import CommonSuccessView, CommonErrorView

logger = get_logger("sumire.cogs.utility.confess")


class ConfessMixin:
    """匿名告白コマンド Mixin"""

    @app_commands.command(name="confess", description="匿名でメッセージを投稿します")
    @app_commands.describe(message="投稿する内容")
    async def confess(
        self,
        interaction: discord.Interaction,
        message: str
    ) -> None:
        """匿名メッセージを投稿"""
        if not interaction.guild:
            view = CommonErrorView(
                title="エラー",
                description="このコマンドはサーバー内でのみ使用できます。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # 内容の長さチェック
        if len(message) > 2000:
            view = CommonErrorView(
                title="エラー",
                description="メッセージは2000文字以内にしてください。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # 匿名メッセージを投稿
        confess_view = ConfessView(content=message)
        await interaction.channel.send(view=confess_view)

        # 投稿者には確認メッセージ（ephemeral）
        view = CommonSuccessView(
            title="投稿完了",
            description="匿名メッセージを投稿しました。"
        )
        await interaction.response.send_message(view=view, ephemeral=True)

        logger.info(f"匿名メッセージ投稿: {interaction.guild.name} #{interaction.channel.name}")
