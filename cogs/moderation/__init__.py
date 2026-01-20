"""
Moderation Cog - モデレーションコマンド
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import discord
from discord import app_commands
from discord.ext import commands

from utils.config import Config
from utils.database import Database
from utils.logging import get_logger
from utils.checks import handle_app_command_error
from views.moderation_views import LogModerationActionView, ModerationDMView

from .ban import BanMixin
from .kick import KickMixin
from .timeout import TimeoutMixin

if TYPE_CHECKING:
    from bot import SumireBot

logger = get_logger("sumire.cogs.moderation")


class Moderation(BanMixin, KickMixin, TimeoutMixin, commands.Cog):
    """モデレーション機能"""

    def __init__(self, bot: SumireBot) -> None:
        self.bot = bot
        self.config = Config()
        self.db = Database()

    # ==================== ヘルパーメソッド ====================

    async def _get_log_channel(self, guild_id: int) -> Optional[discord.TextChannel]:
        """ログチャンネルを取得"""
        settings = await self.db.get_logger_settings(guild_id)
        if not settings or not settings.get("enabled") or not settings.get("channel_id"):
            return None

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return None

        channel = guild.get_channel(settings["channel_id"])
        if isinstance(channel, discord.TextChannel):
            return channel
        return None

    async def _send_dm_notification(
        self,
        user: discord.User,
        action_type: str,
        guild_name: str,
        reason: str,
        duration: Optional[str] = None
    ) -> bool:
        """DM通知を送信"""
        try:
            view = ModerationDMView(
                action_type=action_type,
                guild_name=guild_name,
                reason=reason,
                duration=duration
            )
            await user.send(view=view)
            return True
        except (discord.Forbidden, discord.HTTPException):
            return False

    async def _send_log(
        self,
        guild_id: int,
        action_type: str,
        target: discord.User,
        moderator: discord.Member,
        reason: str,
        duration: Optional[str] = None
    ) -> None:
        """ログチャンネルに送信"""
        channel = await self._get_log_channel(guild_id)
        if not channel:
            return

        try:
            view = LogModerationActionView(
                action_type=action_type,
                target_name=str(target),
                target_mention=target.mention,
                target_avatar=target.display_avatar.url,
                target_id=target.id,
                moderator_name=str(moderator),
                moderator_mention=moderator.mention,
                reason=reason,
                duration=duration
            )
            await channel.send(view=view)
        except discord.Forbidden:
            logger.warning(f"ログチャンネルへの送信権限がありません: guild_id={guild_id}")

    def _can_moderate(
        self,
        moderator: discord.Member,
        target: discord.Member,
        guild: discord.Guild
    ) -> tuple[bool, Optional[str]]:
        """モデレーション可能かチェック"""
        if moderator.id == target.id:
            return False, "自分自身に対してこの操作はできません。"

        if target.id == guild.owner_id:
            return False, "サーバーオーナーに対してこの操作はできません。"

        bot_member = guild.me
        if target.top_role >= bot_member.top_role:
            return False, "対象ユーザーのロールがBotより上位のため、この操作はできません。"

        if moderator.id != guild.owner_id and target.top_role >= moderator.top_role:
            return False, "対象ユーザーのロールがあなたより上位または同等のため、この操作はできません。"

        return True, None

    @staticmethod
    def _format_duration(minutes: int) -> str:
        """分を読みやすい形式に変換"""
        if minutes < 60:
            return f"{minutes}分"
        elif minutes < 1440:
            hours = minutes // 60
            return f"{hours}時間"
        else:
            days = minutes // 1440
            return f"{days}日"

    # ==================== エラーハンドリング ====================

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ) -> None:
        """コマンドエラーハンドリング"""
        await handle_app_command_error(interaction, error, "Moderation")


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(Moderation(bot))
