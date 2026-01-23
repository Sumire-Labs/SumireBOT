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
    "twitter": {
        "patterns": [
            r"https?://(?:www\.)?(?:twitter\.com|x\.com)/\S+/status/\d+",
        ],
        "replacements": [
            ("twitter.com", "vxtwitter.com"),
            ("x.com", "fixvx.com"),
        ],
    },
    "instagram": {
        "patterns": [
            r"https?://(?:www\.)?instagram\.com/(?:p|reel|reels)/[\w-]+",
        ],
        "replacements": [
            ("instagram.com", "ddinstagram.com"),
        ],
    },
    "tiktok": {
        "patterns": [
            r"https?://(?:www\.)?tiktok\.com/@[\w.]+/video/\d+",
            r"https?://(?:vm|vt)\.tiktok\.com/\w+",
        ],
        "replacements": [
            ("tiktok.com", "vxtiktok.com"),
        ],
    },
    "reddit": {
        "patterns": [
            r"https?://(?:www\.)?reddit\.com/r/\w+/comments/\w+",
        ],
        "replacements": [
            ("reddit.com", "rxddit.com"),
        ],
    },
    "threads": {
        "patterns": [
            r"https?://(?:www\.)?threads\.net/@[\w.]+/post/[\w-]+",
        ],
        "replacements": [
            ("threads.net", "fixthreads.net"),
        ],
    },
    "bluesky": {
        "patterns": [
            r"https?://bsky\.app/profile/[\w.]+/post/\w+",
        ],
        "replacements": [
            ("bsky.app", "bskyx.app"),
        ],
    },
    "pixiv": {
        "patterns": [
            r"https?://(?:www\.)?pixiv\.net/(?:en/)?artworks/\d+",
        ],
        "replacements": [
            ("pixiv.net", "phixiv.net"),
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

        # 各修正URLに対してViewを送信
        for platform, original_url, fixed_url in fixes:
            try:
                view = EmbedFixView(
                    original_user_id=message.author.id,
                    platform=platform,
                    fixed_url=fixed_url,
                    original_url=original_url
                )

                await message.reply(view=view, mention_author=False)

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
