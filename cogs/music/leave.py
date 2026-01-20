"""
Leave コマンド
"""
from __future__ import annotations

import discord
from discord import app_commands

from views.music_views import MusicErrorView, MusicSuccessView


class LeaveMixin:
    """Leave コマンド Mixin"""

    @app_commands.command(name="leave", description="再生を停止してボイスチャンネルから退出します")
    async def leave(self, interaction: discord.Interaction) -> None:
        """再生停止 & 退出"""
        player = await self._get_player(interaction)

        if not player:
            view = MusicErrorView(
                title="エラー",
                description="現在ボイスチャンネルに接続していません。"
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

        # キューをクリアして停止
        player.queue.clear()
        await player.stop()

        # ループモードをリセット
        guild_id = interaction.guild.id
        if guild_id in self.loop_mode:
            del self.loop_mode[guild_id]

        # 自動退出タイマーをキャンセル
        if guild_id in self._auto_leave_tasks:
            self._auto_leave_tasks[guild_id].cancel()
            del self._auto_leave_tasks[guild_id]

        # VCから切断
        await player.disconnect()

        view = MusicSuccessView(
            title="退出",
            description="再生を停止し、ボイスチャンネルから退出しました。"
        )
        await interaction.response.send_message(view=view)
