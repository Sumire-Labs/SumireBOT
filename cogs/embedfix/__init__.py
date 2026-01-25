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
    "twitter": {
        "patterns": [
            r"https?://(?:www\.)?twitter\.com/\w+/status/\d+",
            r"https?://(?:www\.)?x\.com/\w+/status/\d+",
        ],
        "replacements": [
            ("twitter.com", "vxtwitter.com"),
            ("x.com", "vxtwitter.com"),
        ],
    },
    "medal": {
        "patterns": [
            r"https?://(?:www\.)?medal\.tv/[\w/-]+/clips/[\w-]+(?:\?[^\s]*)?",
        ],
        "replacements": [],
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

                # 置換がなくても対応プラットフォームなら結果に追加
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
                # ユーザー情報と日付、元メッセージ内容を含めて送信
                timestamp = discord.utils.format_dt(message.created_at, style="f")

                # 元メッセージの内容（リンク以外のテキスト）
                original_content = message.content
                for _, orig_url, _ in fixes:
                    original_content = original_content.replace(orig_url, "").strip()

                if original_content:
                    content = f"{message.author.mention} ({timestamp})\n{original_content}\n{fixed_url}"
                else:
                    content = f"{message.author.mention} ({timestamp})\n{fixed_url}"

                sent_message = await message.channel.send(content)

                # スター対象チャンネルの場合、手動でスター処理
                star_settings = await self.db.get_star_settings(message.guild.id)
                if star_settings and star_settings.get("enabled", True):
                    target_channels = star_settings.get("target_channels", [])
                    if message.channel.id in target_channels:
                        # ⭐リアクションを追加
                        await sent_message.add_reaction("⭐")
                        # 元のユーザーのauthor_idで記録
                        await self.db.create_star_message(
                            guild_id=message.guild.id,
                            channel_id=message.channel.id,
                            message_id=sent_message.id,
                            author_id=message.author.id  # 元の投稿者
                        )

                # 元メッセージを削除
                try:
                    await message.delete()
                except discord.Forbidden:
                    logger.warning(f"元メッセージ削除権限なし: {message.channel.name}")
                except discord.NotFound:
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
