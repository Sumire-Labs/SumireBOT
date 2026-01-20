"""
Skip コマンド
"""
from __future__ import annotations

import discord
from discord import app_commands

from views.music_views import MusicErrorView, MusicSuccessView


class SkipMixin:
    """Skip コマンド Mixin"""

    @app_commands.command(name="skip", description="現在の曲をスキップします")
    async def skip(self, interaction: discord.Interaction) -> None:
        """曲をスキップ"""
        player = await self._get_player(interaction)

        if not player or not player.playing:
            view = MusicErrorView(
                title="エラー",
                description="現在再生中の曲がありません。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        if not interaction.user.voice or player.channel != interaction.user.voice.channel:
            view = MusicErrorView(
                title="エラー",
                description="Botと同じボイスチャンネルに参加してください。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        current_track = player.current
        await player.skip()

        view = MusicSuccessView(
            title="スキップ",
            description=f"**{current_track.title}** をスキップしました。"
        )
        await interaction.response.send_message(view=view)
