"""
Star 設定コマンド
"""
from __future__ import annotations

import discord
from discord import app_commands

from utils.checks import Checks
from utils.logging import get_logger
from views.common_views import CommonErrorView
from views.star_views import StarSettingsView

logger = get_logger("sumire.cogs.star.settings")


class StarSettingsMixin:
    """Star 設定コマンド Mixin"""

    @app_commands.command(name="star", description="スター評価システムを設定します")
    @app_commands.default_permissions(administrator=True)
    @Checks.is_admin()
    async def star_settings(self, interaction: discord.Interaction) -> None:
        """スター評価設定コマンド"""
        if not interaction.guild:
            view = CommonErrorView(
                title="エラー",
                description="このコマンドはサーバー内でのみ使用できます。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        settings = await self.db.get_star_settings(interaction.guild.id)
        enabled = bool(settings.get("enabled", 1)) if settings else True
        target_channels = settings.get("target_channels", []) if settings else []
        weekly_report_channel_id = settings.get("weekly_report_channel_id") if settings else None

        view = StarSettingsView(
            guild=interaction.guild,
            enabled=enabled,
            target_channels=target_channels,
            weekly_report_channel_id=weekly_report_channel_id
        )

        await interaction.response.send_message(view=view, ephemeral=True)
