"""
Ping コマンド Cog
"""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from utils.config import Config
from utils.embeds import EmbedBuilder


class Ping(commands.Cog):
    """Pingコマンド"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.config = Config()
        self.embed_builder = EmbedBuilder()

    @app_commands.command(name="ping", description="BOTのレイテンシを測定します")
    async def ping(self, interaction: discord.Interaction) -> None:
        """BOTのレイテンシを測定するコマンド"""
        # WebSocketレイテンシ
        ws_latency = round(self.bot.latency * 1000)

        # 応答レイテンシを測定
        await interaction.response.defer()

        embed = self.embed_builder.create(
            title="🏓 Pong!",
            description="BOTのレイテンシ情報"
        )

        # レイテンシに応じた色とステータス
        if ws_latency < 100:
            status = "🟢 良好"
            color = self.config.success_color
        elif ws_latency < 200:
            status = "🟡 普通"
            color = self.config.warning_color
        else:
            status = "🔴 遅延"
            color = self.config.error_color

        embed.color = color
        embed.add_field(
            name="WebSocket",
            value=f"`{ws_latency}ms`",
            inline=True
        )
        embed.add_field(
            name="ステータス",
            value=status,
            inline=True
        )
        embed.set_footer(text=f"リクエスト: {interaction.user}")

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(Ping(bot))
