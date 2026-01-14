"""
Ping コマンド Cog
Components V2 を使用
"""
from __future__ import annotations

import discord
from discord import app_commands, ui
from discord.ext import commands

from utils.config import Config


class PingView(ui.LayoutView):
    """Ping結果表示用View (Components V2)"""

    def __init__(self, latency: int) -> None:
        super().__init__(timeout=300)

        # レイテンシに応じた色とステータス
        if latency < 100:
            status = "🟢 良好"
            color = discord.Colour.green()
        elif latency < 200:
            status = "🟡 普通"
            color = discord.Colour.yellow()
        else:
            status = "🔴 遅延"
            color = discord.Colour.red()

        # Container を作成
        container = ui.Container(accent_colour=color)

        # ヘッダー
        container.add_item(ui.TextDisplay("# 🏓 Pong!"))
        container.add_item(ui.Separator())

        # レイテンシ情報
        container.add_item(ui.TextDisplay(
            f"**WebSocket:** `{latency}ms`\n"
            f"**ステータス:** {status}"
        ))

        self.add_item(container)


class Ping(commands.Cog):
    """Pingコマンド"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.config = Config()

    @app_commands.command(name="ping", description="BOTのレイテンシを測定します")
    async def ping(self, interaction: discord.Interaction) -> None:
        """BOTのレイテンシを測定するコマンド"""
        # WebSocketレイテンシ
        ws_latency = round(self.bot.latency * 1000)

        # Components V2 Viewを作成
        view = PingView(latency=ws_latency)

        await interaction.response.send_message(view=view)


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(Ping(bot))
