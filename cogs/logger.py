"""
ログシステム Cog
サーバーイベントをログチャンネルに記録
"""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Union

from utils.config import Config
from utils.database import Database
from utils.embeds import EmbedBuilder
from utils.checks import Checks
from utils.logging import get_logger

logger = get_logger("sumire.cogs.logger")


class Logger(commands.Cog):
    """サーバーログシステム"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.config = Config()
        self.db = Database()
        self.embed_builder = EmbedBuilder()

    async def _get_log_channel(self, guild_id: int) -> Optional[discord.TextChannel]:
        """ログチャンネルを取得"""
        settings = await self.db.get_logger_settings(guild_id)
        if not settings or not settings.get("enabled") or not settings.get("channel_id"):
            return None

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return None

        return guild.get_channel(settings["channel_id"])

    async def _should_log(self, guild_id: int, log_type: str) -> bool:
        """指定されたログタイプが有効かチェック"""
        settings = await self.db.get_logger_settings(guild_id)
        if not settings or not settings.get("enabled"):
            return False

        type_map = {
            "messages": "log_messages",
            "channels": "log_channels",
            "roles": "log_roles",
            "members": "log_members"
        }

        setting_key = type_map.get(log_type)
        if not setting_key:
            return True  # 未定義のタイプはデフォルトでTrue

        return bool(settings.get(setting_key, True))

    # ==================== コマンド ====================

    @app_commands.command(name="logger", description="サーバーログを設定します")
    @Checks.is_admin()
    async def logger_command(self, interaction: discord.Interaction) -> None:
        """
        ログシステムを設定するコマンド
        実行チャンネルをログ出力先として設定
        """
        await interaction.response.defer(ephemeral=True)

        guild_id = interaction.guild_id
        channel_id = interaction.channel_id

        # 現在の設定を取得
        current_settings = await self.db.get_logger_settings(guild_id)

        if current_settings and current_settings.get("enabled"):
            # 既に有効な場合は、トグル or 設定変更
            if current_settings.get("channel_id") == channel_id:
                # 同じチャンネルなら無効化
                await self.db.disable_logger(guild_id)
                embed = self.embed_builder.warning(
                    title="ログシステムを無効化しました",
                    description="サーバーログの記録を停止しました。"
                )
            else:
                # 別チャンネルなら更新
                await self.db.set_logger_channel(guild_id, channel_id)
                embed = self.embed_builder.success(
                    title="ログチャンネルを変更しました",
                    description=f"ログ出力先を {interaction.channel.mention} に変更しました。"
                )
        else:
            # 新規設定
            await self.db.set_logger_channel(guild_id, channel_id)
            embed = self.embed_builder.success(
                title="ログシステムを有効化しました",
                description=f"サーバーログを {interaction.channel.mention} に出力します。"
            )

            embed.add_field(
                name="📋 記録されるイベント",
                value="• 📝 メッセージ（作成/編集/削除）\n"
                      "• 📢 チャンネル（作成/変更/削除）\n"
                      "• 🎭 ロール（作成/変更/削除）\n"
                      "• 👤 メンバー（参加/退出/Ban/Unban）",
                inline=False
            )

        await interaction.followup.send(embed=embed)
        logger.info(f"ログ設定変更: guild_id={guild_id}, channel_id={channel_id}")

    # ==================== メッセージイベント ====================

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """メッセージ削除イベント"""
        if not message.guild or message.author.bot:
            return

        if not await self._should_log(message.guild.id, "messages"):
            return

        channel = await self._get_log_channel(message.guild.id)
        if not channel:
            return

        content = message.content or "*内容なし*"
        if len(content) > 1024:
            content = content[:1021] + "..."

        embed = self.embed_builder.log_message_delete(message, content)

        # 添付ファイル情報
        if message.attachments:
            attachments = "\n".join([a.filename for a in message.attachments])
            embed.add_field(name="添付ファイル", value=attachments[:1024], inline=False)

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"ログ送信権限なし: guild_id={message.guild.id}")

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        """メッセージ編集イベント"""
        if not after.guild or after.author.bot:
            return

        # 内容が変わっていない場合はスキップ（ピン留め等）
        if before.content == after.content:
            return

        if not await self._should_log(after.guild.id, "messages"):
            return

        channel = await self._get_log_channel(after.guild.id)
        if not channel:
            return

        embed = self.embed_builder.log_message_edit(before, after)

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"ログ送信権限なし: guild_id={after.guild.id}")

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[discord.Message]) -> None:
        """一括メッセージ削除イベント"""
        if not messages:
            return

        guild = messages[0].guild
        if not guild:
            return

        if not await self._should_log(guild.id, "messages"):
            return

        channel = await self._get_log_channel(guild.id)
        if not channel:
            return

        embed = self.embed_builder.create(
            title="📝 メッセージ一括削除",
            description=f"**{len(messages)}** 件のメッセージが削除されました",
            color=self.config.error_color
        )
        embed.add_field(
            name="チャンネル",
            value=messages[0].channel.mention if messages[0].channel else "不明",
            inline=True
        )

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"ログ送信権限なし: guild_id={guild.id}")

    # ==================== メンバーイベント ====================

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """メンバー参加イベント"""
        if not await self._should_log(member.guild.id, "members"):
            return

        channel = await self._get_log_channel(member.guild.id)
        if not channel:
            return

        embed = self.embed_builder.log_member_join(member)

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"ログ送信権限なし: guild_id={member.guild.id}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """メンバー退出イベント"""
        if not await self._should_log(member.guild.id, "members"):
            return

        channel = await self._get_log_channel(member.guild.id)
        if not channel:
            return

        embed = self.embed_builder.log_member_leave(member)

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"ログ送信権限なし: guild_id={member.guild.id}")

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: Union[discord.Member, discord.User]) -> None:
        """メンバーBanイベント"""
        if not await self._should_log(guild.id, "members"):
            return

        channel = await self._get_log_channel(guild.id)
        if not channel:
            return

        embed = self.embed_builder.log_member_ban(guild, user)

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"ログ送信権限なし: guild_id={guild.id}")

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User) -> None:
        """メンバーUnbanイベント"""
        if not await self._should_log(guild.id, "members"):
            return

        channel = await self._get_log_channel(guild.id)
        if not channel:
            return

        embed = self.embed_builder.log_member_unban(guild, user)

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"ログ送信権限なし: guild_id={guild.id}")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """メンバー更新イベント（タイムアウト等）"""
        if not await self._should_log(after.guild.id, "members"):
            return

        channel = await self._get_log_channel(after.guild.id)
        if not channel:
            return

        # タイムアウトの検出
        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until:
                embed = self.embed_builder.create(
                    title="⏰ メンバータイムアウト",
                    description=f"{after.mention} がタイムアウトされました",
                    color=self.config.warning_color
                )
                embed.add_field(
                    name="解除予定",
                    value=discord.utils.format_dt(after.timed_out_until, "R"),
                    inline=True
                )
            else:
                embed = self.embed_builder.create(
                    title="⏰ タイムアウト解除",
                    description=f"{after.mention} のタイムアウトが解除されました",
                    color=self.config.success_color
                )

            embed.set_author(name=str(after), icon_url=after.display_avatar.url)
            embed.set_footer(text=f"ユーザーID: {after.id}")

            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                logger.warning(f"ログ送信権限なし: guild_id={after.guild.id}")

    # ==================== チャンネルイベント ====================

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        """チャンネル作成イベント"""
        if not await self._should_log(channel.guild.id, "channels"):
            return

        log_channel = await self._get_log_channel(channel.guild.id)
        if not log_channel:
            return

        embed = self.embed_builder.log_channel_create(channel)

        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"ログ送信権限なし: guild_id={channel.guild.id}")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        """チャンネル削除イベント"""
        if not await self._should_log(channel.guild.id, "channels"):
            return

        log_channel = await self._get_log_channel(channel.guild.id)
        if not log_channel:
            return

        embed = self.embed_builder.log_channel_delete(channel)

        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"ログ送信権限なし: guild_id={channel.guild.id}")

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self,
        before: discord.abc.GuildChannel,
        after: discord.abc.GuildChannel
    ) -> None:
        """チャンネル更新イベント"""
        if not await self._should_log(after.guild.id, "channels"):
            return

        log_channel = await self._get_log_channel(after.guild.id)
        if not log_channel:
            return

        changes = []

        if before.name != after.name:
            changes.append(f"**名前:** {before.name} → {after.name}")

        if hasattr(before, "topic") and hasattr(after, "topic"):
            if before.topic != after.topic:
                changes.append(f"**トピック:** 変更されました")

        if not changes:
            return

        embed = self.embed_builder.create(
            title="📢 チャンネル更新",
            description=f"**チャンネル:** {after.mention}",
            color=self.config.warning_color
        )
        embed.add_field(name="変更内容", value="\n".join(changes), inline=False)
        embed.set_footer(text=f"チャンネルID: {after.id}")

        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"ログ送信権限なし: guild_id={after.guild.id}")

    # ==================== ロールイベント ====================

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role) -> None:
        """ロール作成イベント"""
        if not await self._should_log(role.guild.id, "roles"):
            return

        channel = await self._get_log_channel(role.guild.id)
        if not channel:
            return

        embed = self.embed_builder.log_role_create(role)

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"ログ送信権限なし: guild_id={role.guild.id}")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role) -> None:
        """ロール削除イベント"""
        if not await self._should_log(role.guild.id, "roles"):
            return

        channel = await self._get_log_channel(role.guild.id)
        if not channel:
            return

        embed = self.embed_builder.log_role_delete(role)

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"ログ送信権限なし: guild_id={role.guild.id}")

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role) -> None:
        """ロール更新イベント"""
        if not await self._should_log(after.guild.id, "roles"):
            return

        channel = await self._get_log_channel(after.guild.id)
        if not channel:
            return

        changes = []

        if before.name != after.name:
            changes.append(f"**名前:** {before.name} → {after.name}")

        if before.color != after.color:
            changes.append(f"**色:** #{before.color.value:06x} → #{after.color.value:06x}")

        if before.permissions != after.permissions:
            changes.append("**権限:** 変更されました")

        if not changes:
            return

        embed = self.embed_builder.create(
            title="🎭 ロール更新",
            description=f"**ロール:** {after.mention}",
            color=after.color if after.color.value else self.config.warning_color
        )
        embed.add_field(name="変更内容", value="\n".join(changes), inline=False)
        embed.set_footer(text=f"ロールID: {after.id}")

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"ログ送信権限なし: guild_id={after.guild.id}")

    # ==================== エラーハンドリング ====================

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ) -> None:
        """コマンドエラーハンドリング"""
        if isinstance(error, app_commands.CheckFailure):
            embed = self.embed_builder.error(
                title="権限エラー",
                description="このコマンドを実行する権限がありません。\n"
                           "管理者権限が必要です。"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            logger.error(f"コマンドエラー: {error}")
            embed = self.embed_builder.error(
                title="エラー",
                description="コマンドの実行中にエラーが発生しました。"
            )
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(Logger(bot))
