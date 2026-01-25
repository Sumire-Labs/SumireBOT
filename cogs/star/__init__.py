"""
Star Rating Cog - スター評価システム
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands

from utils.config import Config
from utils.database import Database
from utils.checks import handle_app_command_error

from .settings import StarSettingsMixin
from .events import StarEventsMixin
from .leaderboard import StarLeaderboardMixin
from .info import StarInfoMixin
from .weekly_report import StarWeeklyReportMixin

if TYPE_CHECKING:
    from bot import SumireBot


class Star(
    StarSettingsMixin,
    StarEventsMixin,
    StarLeaderboardMixin,
    StarInfoMixin,
    StarWeeklyReportMixin,
    commands.Cog
):
    """スター評価システム"""

    def __init__(self, bot: SumireBot) -> None:
        self.bot = bot
        self.config = Config()
        self.db = Database()

    async def cog_load(self) -> None:
        """Cog読み込み時"""
        self.start_weekly_report_task()

    async def cog_unload(self) -> None:
        """Cog解除時"""
        self.stop_weekly_report_task()

    async def cog_app_command_error(
        self,
        interaction,
        error: app_commands.AppCommandError
    ) -> None:
        """コマンドエラーハンドリング"""
        await handle_app_command_error(interaction, error, "Star")


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(Star(bot))
