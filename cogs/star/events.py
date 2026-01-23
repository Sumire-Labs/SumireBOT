"""
Star イベントリスナー
"""
from __future__ import annotations

import discord
from discord.ext import commands

from utils.logging import get_logger

logger = get_logger("sumire.cogs.star.events")

# スター絵文字
STAR_EMOJI = "⭐"


class StarEventsMixin:
    """Star イベントリスナー Mixin"""

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """対象チャンネルへのメッセージにスターリアクションを追加"""
        # Bot・DM除外
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id

        # スター設定を取得
        settings = await self.db.get_star_settings(guild_id)
        if not settings or not settings.get("enabled", True):
            return

        # 対象チャンネルかチェック
        target_channels = settings.get("target_channels", [])
        if message.channel.id not in target_channels:
            return

        # メディア（画像・動画・埋め込み）があるメッセージのみ対象
        if not message.attachments and not message.embeds:
            return

        try:
            # スターリアクションを追加
            await message.add_reaction(STAR_EMOJI)

            # データベースにメッセージを記録
            await self.db.create_star_message(
                guild_id=guild_id,
                channel_id=message.channel.id,
                message_id=message.id,
                author_id=message.author.id
            )

            logger.debug(f"スター追加: {message.id} in {message.channel.name}")

        except discord.Forbidden:
            logger.warning(f"スターリアクション追加権限なし: {message.channel.name}")
        except Exception as e:
            logger.error(f"スターリアクション追加エラー: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """スターリアクション追加時のカウント処理"""
        # DMは除外
        if not payload.guild_id:
            return

        # スター絵文字のみ対象
        if str(payload.emoji) != STAR_EMOJI:
            return

        # Botのリアクションは除外（自分自身の追加を含む）
        if payload.user_id == self.bot.user.id:
            return

        if payload.member and payload.member.bot:
            return

        guild_id = payload.guild_id
        message_id = payload.message_id
        user_id = payload.user_id

        # スター設定を確認
        settings = await self.db.get_star_settings(guild_id)
        if not settings or not settings.get("enabled", True):
            return

        # 対象チャンネルかチェック
        target_channels = settings.get("target_channels", [])
        if payload.channel_id not in target_channels:
            return

        # スターメッセージを取得
        star_msg = await self.db.get_star_message(message_id)
        if not star_msg:
            return

        # 自己評価は除外
        if user_id == star_msg["author_id"]:
            return

        # スターを追加
        added = await self.db.add_star(message_id, user_id)
        if added:
            logger.debug(f"スターカウント追加: {message_id} by {user_id}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        """スターリアクション削除時のカウント処理"""
        # DMは除外
        if not payload.guild_id:
            return

        # スター絵文字のみ対象
        if str(payload.emoji) != STAR_EMOJI:
            return

        # Botは除外
        if payload.user_id == self.bot.user.id:
            return

        guild_id = payload.guild_id
        message_id = payload.message_id
        user_id = payload.user_id

        # スター設定を確認
        settings = await self.db.get_star_settings(guild_id)
        if not settings or not settings.get("enabled", True):
            return

        # 対象チャンネルかチェック
        target_channels = settings.get("target_channels", [])
        if payload.channel_id not in target_channels:
            return

        # スターを削除
        removed = await self.db.remove_star(message_id, user_id)
        if removed:
            logger.debug(f"スターカウント削除: {message_id} by {user_id}")
