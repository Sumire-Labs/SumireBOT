"""
EmbedFix Cog - ソーシャルメディア埋め込み修正
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional

import discord
from discord import app_commands
from discord.ext import commands

from utils.config import Config
from utils.database import Database
from utils.checks import handle_app_command_error
from utils.logging import get_logger
from views.embedfix_views import EmbedFixView

if TYPE_CHECKING:
    from bot import SumireBot

logger = get_logger("sumire.cogs.embedfix")


# 対応プラットフォームと修正URL
PLATFORM_FIXES = {
    "instagram": {
        "patterns": [
            r"https?://(?:www\.)?instagram\.com/(?:p|reel|reels)/[\w-]+",
        ],
        "replacements": [
            ("instagram.com", "vxinstagram.com"),
        ],
    },
}


def detect_and_fix_url(content: str) -> list[tuple[str, str, str]]:
    """
    メッセージ内のソーシャルメディアURLを検出して修正版を返す

    Returns:
        list[tuple[str, str, str]]: [(platform, original_url, fixed_url), ...]
    """
    results = []

    for platform, config in PLATFORM_FIXES.items():
        for pattern in config["patterns"]:
            matches = re.findall(pattern, content)
            for original_url in matches:
                fixed_url = original_url
                for old, new in config["replacements"]:
                    fixed_url = fixed_url.replace(old, new)

                if fixed_url != original_url:
                    results.append((platform, original_url, fixed_url))

    return results


class EmbedFix(commands.Cog):
    """ソーシャルメディア埋め込み修正"""

    def __init__(self, bot: SumireBot) -> None:
        self.bot = bot
        self.config = Config()
        self.db = Database()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """メッセージ内のソーシャルメディアURLを検出して修正"""
        # Bot・DM除外
        if message.author.bot or not message.guild:
            return

        # URLを検出・修正
        fixes = detect_and_fix_url(message.content)
        if not fixes:
            return

        # 各修正URLに対してメッセージを送信
        for platform, original_url, fixed_url in fixes:
            try:
                # 通常メッセージとして送信（Discordが自動で埋め込み生成）
                await message.reply(fixed_url, mention_author=False)

                # 元メッセージの埋め込みを抑制
                try:
                    await message.edit(suppress=True)
                except discord.Forbidden:
                    pass

                logger.debug(f"埋め込み修正: {platform} - {message.author}")

            except Exception as e:
                logger.error(f"埋め込み修正エラー: {e}")

    async def cog_app_command_error(
        self,
        interaction,
        error: app_commands.AppCommandError
    ) -> None:
        """コマンドエラーハンドリング"""
        await handle_app_command_error(interaction, error, "EmbedFix")


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(EmbedFix(bot))
