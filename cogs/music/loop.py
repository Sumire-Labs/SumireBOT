"""
Loop コマンド
"""
from __future__ import annotations

import discord
from discord import app_commands

from views.music_views import MusicErrorView, MusicSuccessView


class LoopMixin:
    """Loop コマンド Mixin"""

    @app_commands.command(name="loop", description="ループモードを切り替えます")
    @app_commands.describe(mode="ループモード")
    @app_commands.choices(mode=[
        app_commands.Choice(name="オフ", value="off"),
        app_commands.Choice(name="トラック", value="track"),
        app_commands.Choice(name="キュー", value="queue"),
    ])
    async def loop(self, interaction: discord.Interaction, mode: str) -> None:
        """ループモードを設定"""
        player = await self._get_player(interaction)

        if not player:
            view = MusicErrorView(
                title="エラー",
                description="現在再生中ではありません。"
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

        guild_id = interaction.guild.id
        self.loop_mode[guild_id] = mode

        mode_text = {
            "off": "オフ",
            "track": "🔂 トラック（1曲リピート）",
            "queue": "🔁 キュー（全曲リピート）"
        }

        view = MusicSuccessView(
            title="ループ設定",
            description=f"ループモードを **{mode_text[mode]}** に設定しました。"
        )
        await interaction.response.send_message(view=view)
