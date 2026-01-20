"""
Admin Cog - 管理コマンド（AutoRole, Owner）
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands

from utils.config import Config
from utils.database import Database
from utils.embeds import EmbedBuilder
from utils.checks import handle_app_command_error

from .autorole import AutoRoleMixin
from .owner import OwnerMixin

if TYPE_CHECKING:
    from bot import SumireBot


class Admin(AutoRoleMixin, OwnerMixin, commands.Cog):
    """管理コマンド"""

    def __init__(self, bot: SumireBot) -> None:
        self.bot = bot
        self.config = Config()
        self.db = Database()
        self.embed_builder = EmbedBuilder()

    # ==================== エラーハンドリング ====================

    async def cog_app_command_error(
        self,
        interaction,
        error: app_commands.AppCommandError
    ) -> None:
        """コマンドエラーハンドリング"""
        await handle_app_command_error(interaction, error, "Admin")


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(Admin(bot))
