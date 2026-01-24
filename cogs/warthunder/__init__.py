"""
WarThunder Cog - War Thunder関連機能
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from utils.config import Config
from utils.checks import handle_app_command_error
from views.br_roulette_views import BRRouletteView
from .br_roulette import BRRouletteMixin

if TYPE_CHECKING:
    from bot import SumireBot


class WarThunder(BRRouletteMixin, commands.Cog):
    """War Thunder関連機能"""

    def __init__(self, bot: SumireBot) -> None:
        self.bot = bot
        self.config = Config()

    async def cog_load(self) -> None:
        """Cog読み込み時に永続的Viewを登録"""
        self.bot.add_view(BRRouletteView(self.bot))

    async def cog_app_command_error(
        self,
        interaction,
        error
    ) -> None:
        """コマンドエラーハンドリング"""
        await handle_app_command_error(interaction, error, "WarThunder")


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(WarThunder(bot))
