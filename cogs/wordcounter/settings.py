"""
WordCounter 設定コマンド
"""
from __future__ import annotations

import discord
from discord import app_commands

from utils.checks import Checks
from utils.logging import get_logger
from views.common_views import CommonErrorView
from views.wordcounter_views import WordCounterSettingsView

logger = get_logger("sumire.cogs.wordcounter.settings")


class WordCounterSettingsMixin:
    """WordCounter 設定コマンド Mixin"""

    @app_commands.command(name="counter", description="単語カウンターを設定します")
    @app_commands.default_permissions(administrator=True)
    @Checks.is_admin()
    async def counter_settings(self, interaction: discord.Interaction) -> None:
        """単語カウンター設定コマンド"""
        if not interaction.guild:
            view = CommonErrorView(
                title="エラー",
                description="このコマンドはサーバー内でのみ使用できます。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        settings = await self.db.get_wordcounter_settings(interaction.guild.id)
        enabled = bool(settings.get("enabled", 1)) if settings else True
        words = settings.get("words", []) if settings else []

        view = WordCounterSettingsView(
            guild=interaction.guild,
            enabled=enabled,
            words=words
        )

        await interaction.response.send_message(view=view, ephemeral=True)
