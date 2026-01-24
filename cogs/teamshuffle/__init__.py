"""
TeamShuffle Cog - チーム分けくじ
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from utils.config import Config
from utils.database import Database
from utils.checks import handle_app_command_error
from views.teamshuffle_views import TeamShufflePanelView
from .teamshuffle import TeamShuffleMixin

if TYPE_CHECKING:
    from bot import SumireBot


class TeamShuffle(TeamShuffleMixin, commands.Cog):
    """チーム分けくじ機能"""

    def __init__(self, bot: SumireBot) -> None:
        self.bot = bot
        self.config = Config()
        self.db = Database()

    async def cog_load(self) -> None:
        """Cog読み込み時に永続的Viewを登録"""
        self.bot.add_view(TeamShufflePanelView(self.bot))

    async def cog_app_command_error(
        self,
        interaction,
        error
    ) -> None:
        """コマンドエラーハンドリング"""
        await handle_app_command_error(interaction, error, "TeamShuffle")


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(TeamShuffle(bot))
