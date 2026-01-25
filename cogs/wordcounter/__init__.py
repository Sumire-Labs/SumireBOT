"""
WordCounter Cog - 単語カウンターシステム
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands

from utils.config import Config
from utils.database import Database
from utils.checks import handle_app_command_error

from .settings import WordCounterSettingsMixin
from .events import WordCounterEventsMixin
from .leaderboard import WordCounterLeaderboardMixin

if TYPE_CHECKING:
    from bot import SumireBot


class WordCounter(
    WordCounterSettingsMixin,
    WordCounterEventsMixin,
    WordCounterLeaderboardMixin,
    commands.Cog
):
    """単語カウンターシステム"""

    def __init__(self, bot: SumireBot) -> None:
        self.bot = bot
        self.config = Config()
        self.db = Database()

    async def cog_app_command_error(
        self,
        interaction,
        error: app_commands.AppCommandError
    ) -> None:
        """コマンドエラーハンドリング"""
        await handle_app_command_error(interaction, error, "WordCounter")


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(WordCounter(bot))
