"""
Star 情報コマンド
"""
from __future__ import annotations

import discord
from discord import app_commands

from utils.logging import get_logger
from views.common_views import CommonErrorView
from views.star_views import StarInfoView

logger = get_logger("sumire.cogs.star.info")


class StarInfoMixin:
    """Star 情報コマンド Mixin"""

    @app_commands.command(name="starinfo", description="メッセージのスター情報を表示します")
    @app_commands.describe(message_id="確認するメッセージのID")
    async def star_info(
        self,
        interaction: discord.Interaction,
        message_id: str
    ) -> None:
        """メッセージのスター情報を表示"""
        if not interaction.guild:
            view = CommonErrorView(
                title="エラー",
                description="このコマンドはサーバー内でのみ使用できます。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # メッセージIDをパース
        try:
            msg_id = int(message_id)
        except ValueError:
            view = CommonErrorView(
                title="エラー",
                description="無効なメッセージIDです。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # スターメッセージを取得
        star_data = await self.db.get_star_message(msg_id)
        if not star_data:
            view = CommonErrorView(
                title="エラー",
                description="このメッセージはスター対象として記録されていません。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # サーバーが一致するか確認
        if star_data["guild_id"] != interaction.guild.id:
            view = CommonErrorView(
                title="エラー",
                description="このメッセージは他のサーバーのものです。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # メッセージのプレビューを取得（オプション）
        message_preview = None
        try:
            channel = interaction.guild.get_channel(star_data["channel_id"])
            if channel:
                message = await channel.fetch_message(msg_id)
                if message.content:
                    message_preview = message.content
        except Exception:
            pass

        view = StarInfoView(
            guild=interaction.guild,
            star_data=star_data,
            message_preview=message_preview
        )

        await interaction.response.send_message(view=view)
