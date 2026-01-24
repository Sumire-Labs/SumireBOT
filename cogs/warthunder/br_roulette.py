"""
War Thunder BRルーレットコマンド
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands

from views.br_roulette_views import BRRouletteView

if TYPE_CHECKING:
    from bot import SumireBot


class BRRouletteMixin:
    """BRルーレットコマンド Mixin"""

    bot: SumireBot

    @app_commands.command(name="br-roulette", description="War Thunder BRルーレットを開始します")
    @app_commands.describe(mode="モード選択（空/陸）")
    @app_commands.choices(mode=[
        app_commands.Choice(name="🛩️ 空", value="air"),
        app_commands.Choice(name="🚛 陸", value="ground"),
    ])
    @app_commands.guild_only()
    async def br_roulette(
        self,
        interaction: discord.Interaction,
        mode: str = "air"
    ) -> None:
        """BRルーレットパネルを作成"""
        # パネルViewを作成
        panel_view = BRRouletteView(
            bot=self.bot,
            mode=mode,
            current_br=None,
            exclusion_text="",
            excluded_brs=[],
            history=[]
        )

        # パネルを送信
        await interaction.response.send_message(view=panel_view)
