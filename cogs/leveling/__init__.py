"""
Leveling Cog - レベルシステム
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands

from utils.config import Config
from utils.database import Database
from utils.embeds import EmbedBuilder
from utils.checks import handle_app_command_error

from .rank import RankMixin
from .leaderboard import LeaderboardMixin
from .settings import SettingsMixin
from .events import EventsMixin

if TYPE_CHECKING:
    from bot import SumireBot


class Leveling(RankMixin, LeaderboardMixin, SettingsMixin, EventsMixin, commands.Cog):
    """レベルシステム"""

    def __init__(self, bot: SumireBot) -> None:
        self.bot = bot
        self.config = Config()
        self.db = Database()
        self.embed_builder = EmbedBuilder()

    # ==================== ヘルパーメソッド ====================

    def _format_time(self, seconds: int) -> str:
        """秒数を時間:分:秒形式にフォーマット"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}時間{minutes}分"
        elif minutes > 0:
            return f"{minutes}分{secs}秒"
        else:
            return f"{secs}秒"

    # ==================== エラーハンドリング ====================

    async def cog_app_command_error(
        self,
        interaction,
        error: app_commands.AppCommandError
    ) -> None:
        """コマンドエラーハンドリング"""
        await handle_app_command_error(interaction, error, "Leveling")


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(Leveling(bot))
