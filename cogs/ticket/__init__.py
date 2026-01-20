"""
Ticket Cog - チケットシステム
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands

from utils.config import Config
from utils.database import Database
from utils.embeds import EmbedBuilder
from utils.checks import handle_app_command_error

from .ticket import TicketMixin

if TYPE_CHECKING:
    from bot import SumireBot


class Ticket(TicketMixin, commands.Cog):
    """チケットシステム"""

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
        await handle_app_command_error(interaction, error, "Ticket")


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(Ticket(bot))
