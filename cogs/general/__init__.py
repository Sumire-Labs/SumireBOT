"""
General Cog - 一般コマンド
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from utils.config import Config
from .ping import PingMixin
from .avatar import AvatarMixin
from .profile import ProfileMixin
from .roll import RollMixin

if TYPE_CHECKING:
    from bot import SumireBot


class General(PingMixin, AvatarMixin, ProfileMixin, RollMixin, commands.Cog):
    """一般コマンド"""

    def __init__(self, bot: SumireBot) -> None:
        self.bot = bot
        self.config = Config()


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(General(bot))
