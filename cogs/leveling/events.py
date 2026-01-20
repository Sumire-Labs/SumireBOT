"""
Leveling イベントリスナー
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from utils.logging import get_logger

logger = get_logger("sumire.cogs.leveling.events")

# XP設定
XP_MIN = 10
XP_MAX = 25
XP_COOLDOWN_SECONDS = 60


class EventsMixin:
    """Leveling イベントリスナー Mixin"""

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """メッセージ送信時のXP獲得処理"""
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        user_id = message.author.id

        settings = await self.db.get_leveling_settings(guild_id)
        if settings and not settings.get("enabled", True):
            return

        ignored_channels = settings.get("ignored_channels", []) if settings else []
        if message.channel.id in ignored_channels:
            return

        last_xp_time = await self.db.get_user_last_xp_time(guild_id, user_id)
        if last_xp_time:
            cooldown_end = last_xp_time + timedelta(seconds=XP_COOLDOWN_SECONDS)
            if datetime.utcnow() < cooldown_end:
                return

        xp_amount = random.randint(XP_MIN, XP_MAX)
        new_xp, new_level, leveled_up = await self.db.add_user_xp(guild_id, user_id, xp_amount)

        if leveled_up:
            logger.info(f"レベルアップ: {message.author} -> Lv.{new_level} in {message.guild.name}")

    @commands.Cog.listener()
    async def on_leveling_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ) -> None:
        """VC参加/退出時の時間トラッキング"""
        if member.bot:
            return

        guild_id = member.guild.id
        user_id = member.id

        settings = await self.db.get_leveling_settings(guild_id)
        if settings and not settings.get("enabled", True):
            return

        if before.channel is None and after.channel is not None:
            await self.db.set_vc_join_time(guild_id, user_id)
            logger.debug(f"VC参加: {member} in {after.channel.name}")

        elif before.channel is not None and after.channel is None:
            vc_time, vc_level, leveled_up = await self.db.add_vc_time(guild_id, user_id)
            if leveled_up:
                logger.info(f"VCレベルアップ: {member} -> VCLv.{vc_level} in {member.guild.name}")

        elif before.channel is not None and after.channel is not None and before.channel != after.channel:
            logger.debug(f"VC移動: {member} {before.channel.name} -> {after.channel.name}")
