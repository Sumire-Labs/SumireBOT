"""
Utility Cog - ユーティリティコマンド（Translate, Logger）
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands

from utils.config import Config
from utils.database import Database
from utils.checks import handle_app_command_error

from .translate import TranslateMixin
from .logger import LoggerMixin
from .confess import ConfessMixin
from .context_menus import ContextMenusMixin
from .shorturl import ShortUrlMixin

if TYPE_CHECKING:
    from bot import SumireBot


class Utility(TranslateMixin, LoggerMixin, ConfessMixin, ContextMenusMixin, ShortUrlMixin, commands.Cog):
    """ユーティリティ機能"""

    def __init__(self, bot: SumireBot) -> None:
        self.bot = bot
        self.config = Config()
        self.db = Database()

        # 翻訳機能の初期化
        self._init_translator()

    # ==================== エラーハンドリング ====================

    async def cog_app_command_error(
        self,
        interaction,
        error: app_commands.AppCommandError
    ) -> None:
        """コマンドエラーハンドリング"""
        await handle_app_command_error(interaction, error, "Utility")


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(Utility(bot))
