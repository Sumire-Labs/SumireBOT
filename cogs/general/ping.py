"""
Ping コマンド
"""
from __future__ import annotations

import discord
from discord import app_commands, ui


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

        container = ui.Container(accent_colour=color)
        container.add_item(ui.TextDisplay("# 🏓 Pong!"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(
            f"**WebSocket:** `{latency}ms`\n"
            f"**ステータス:** {status}"
        ))
        self.add_item(container)


class PingMixin:
    """Pingコマンド Mixin"""

    @app_commands.command(name="ping", description="BOTのレイテンシを測定します")
    async def ping(self, interaction: discord.Interaction) -> None:
        """BOTのレイテンシを測定"""
        ws_latency = round(self.bot.latency * 1000)
        view = PingView(latency=ws_latency)
        await interaction.response.send_message(view=view)
