"""
ログシステム コマンドとイベント
"""
from __future__ import annotations

from typing import Optional, Union

import discord
from discord import app_commands, ui
from discord.ext import commands

from utils.checks import Checks
from utils.logging import get_logger
from views.common_views import CommonSuccessView, CommonWarningView, CommonErrorView
from views.log_views import (
    LogMessageDeleteView,
    LogMessageEditView,
    LogMemberJoinView,
    LogMemberLeaveView,
    LogMemberBanView,
    LogChannelView,
    LogRoleView,
    LogBulkDeleteView,
    LogMemberTimeoutView,
    LogChannelUpdateView,
    LogRoleUpdateView
)

logger = get_logger("sumire.cogs.utility.logger")


class LoggerMixin:
    """ログシステム Mixin"""

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
            return True

        return bool(settings.get(setting_key, True))

    def _get_channel_type_name(self, channel: discord.abc.GuildChannel) -> str:
        """チャンネルタイプの日本語名を取得"""
        type_names = {
            discord.ChannelType.text: "テキストチャンネル",
            discord.ChannelType.voice: "ボイスチャンネル",
            discord.ChannelType.category: "カテゴリ",
            discord.ChannelType.news: "ニュースチャンネル",
            discord.ChannelType.stage_voice: "ステージチャンネル",
            discord.ChannelType.forum: "フォーラムチャンネル",
        }
        return type_names.get(channel.type, str(channel.type))

    # ==================== コマンド ====================

    @app_commands.command(name="logger", description="サーバーログを設定します")
    @app_commands.default_permissions(administrator=True)
    @Checks.is_admin()
    async def logger_command(self, interaction: discord.Interaction) -> None:
        """ログシステムを設定するコマンド"""
        await interaction.response.defer(ephemeral=True)

        guild_id = interaction.guild_id
        channel_id = interaction.channel_id

        current_settings = await self.db.get_logger_settings(guild_id)

        if current_settings and current_settings.get("enabled"):
            if current_settings.get("channel_id") == channel_id:
                await self.db.disable_logger(guild_id)
                view = CommonWarningView(
                    title="ログシステムを無効化しました",
                    description="サーバーログの記録を停止しました。"
                )
            else:
                await self.db.set_logger_channel(guild_id, channel_id)
                view = CommonSuccessView(
                    title="ログチャンネルを変更しました",
                    description=f"ログ出力先を {interaction.channel.mention} に変更しました。"
                )
        else:
            await self.db.set_logger_channel(guild_id, channel_id)
            view = self._create_logger_enabled_view(interaction.channel.mention)

        await interaction.followup.send(view=view)
        logger.info(f"ログ設定変更: guild_id={guild_id}, channel_id={channel_id}")

    def _create_logger_enabled_view(self, channel_mention: str) -> ui.LayoutView:
        """ログシステム有効化時のView"""
        view = ui.LayoutView(timeout=300)
        container = ui.Container(accent_colour=discord.Colour.green())

        container.add_item(ui.TextDisplay("# ✅ ログシステムを有効化しました"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"サーバーログを {channel_mention} に出力します。"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(
            "**📋 記録されるイベント**\n"
            "• 📝 メッセージ（作成/編集/削除）\n"
            "• 📢 チャンネル（作成/変更/削除）\n"
            "• 🎭 ロール（作成/変更/削除）\n"
            "• 👤 メンバー（参加/退出/Ban/Unban）"
        ))

        view.add_item(container)
        return view

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

        content = message.content or ""
        if message.attachments:
            attachments = "\n".join([f"📎 {a.filename}" for a in message.attachments])
            if content:
                content += f"\n\n{attachments}"
            else:
                content = attachments

        view = LogMessageDeleteView(
            author_name=str(message.author),
            author_avatar=message.author.display_avatar.url,
            author_id=message.author.id,
            channel_mention=message.channel.mention,
            content=content
        )

        try:
            await channel.send(view=view)
        except discord.Forbidden:
            logger.warning(f"ログ送信権限なし: guild_id={message.guild.id}")

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        """メッセージ編集イベント"""
        if not after.guild or after.author.bot:
            return

        if before.content == after.content:
            return

        if not await self._should_log(after.guild.id, "messages"):
            return

        channel = await self._get_log_channel(after.guild.id)
        if not channel:
            return

        view = LogMessageEditView(
            author_name=str(after.author),
            author_avatar=after.author.display_avatar.url,
            author_id=after.author.id,
            channel_mention=after.channel.mention,
            jump_url=after.jump_url,
            before_content=before.content or "",
            after_content=after.content or ""
        )

        try:
            await channel.send(view=view)
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

        channel_mention = messages[0].channel.mention if messages[0].channel else "不明"
        view = LogBulkDeleteView(
            message_count=len(messages),
            channel_mention=channel_mention
        )

        try:
            await channel.send(view=view)
        except discord.Forbidden:
            logger.warning(f"ログ送信権限なし: guild_id={guild.id}")

    # ==================== メンバーイベント ====================

    @commands.Cog.listener()
    async def on_logger_member_join(self, member: discord.Member) -> None:
        """メンバー参加イベント（ログ用）"""
        if not await self._should_log(member.guild.id, "members"):
            return

        channel = await self._get_log_channel(member.guild.id)
        if not channel:
            return

        created_at = discord.utils.format_dt(member.created_at, "R")
        view = LogMemberJoinView(
            member_name=str(member),
            member_mention=member.mention,
            member_avatar=member.display_avatar.url,
            member_id=member.id,
            created_at=created_at,
            member_count=member.guild.member_count
        )

        try:
            await channel.send(view=view)
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

        joined_at = discord.utils.format_dt(member.joined_at, "R") if member.joined_at else "不明"
        roles = [r.name for r in member.roles if r.name != "@everyone"]

        view = LogMemberLeaveView(
            member_name=str(member),
            member_mention=member.mention,
            member_avatar=member.display_avatar.url,
            member_id=member.id,
            joined_at=joined_at,
            roles=roles
        )

        try:
            await channel.send(view=view)
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

        view = LogMemberBanView(
            user_name=str(user),
            user_mention=user.mention,
            user_avatar=user.display_avatar.url,
            user_id=user.id,
            is_unban=False
        )

        try:
            await channel.send(view=view)
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

        view = LogMemberBanView(
            user_name=str(user),
            user_mention=user.mention,
            user_avatar=user.display_avatar.url,
            user_id=user.id,
            is_unban=True
        )

        try:
            await channel.send(view=view)
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
            is_remove = after.timed_out_until is None
            timeout_until = None
            if not is_remove and after.timed_out_until:
                timeout_until = discord.utils.format_dt(after.timed_out_until, "R")

            view = LogMemberTimeoutView(
                member_name=str(after),
                member_mention=after.mention,
                member_avatar=after.display_avatar.url,
                member_id=after.id,
                is_remove=is_remove,
                timeout_until=timeout_until
            )

            try:
                await channel.send(view=view)
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

        view = LogChannelView(
            channel_name=channel.name,
            channel_type=self._get_channel_type_name(channel),
            channel_id=channel.id,
            is_delete=False,
            channel_mention=channel.mention
        )

        try:
            await log_channel.send(view=view)
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

        view = LogChannelView(
            channel_name=channel.name,
            channel_type=self._get_channel_type_name(channel),
            channel_id=channel.id,
            is_delete=True
        )

        try:
            await log_channel.send(view=view)
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

        view = LogChannelUpdateView(
            channel_name=after.name,
            channel_mention=after.mention,
            channel_id=after.id,
            changes=changes
        )

        try:
            await log_channel.send(view=view)
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

        view = LogRoleView(
            role_name=role.name,
            role_id=role.id,
            is_delete=False,
            role_mention=role.mention,
            role_colour=role.colour if role.colour.value else None
        )

        try:
            await channel.send(view=view)
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

        view = LogRoleView(
            role_name=role.name,
            role_id=role.id,
            is_delete=True,
            role_colour=role.colour if role.colour.value else None
        )

        try:
            await channel.send(view=view)
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

        view = LogRoleUpdateView(
            role_name=after.name,
            role_mention=after.mention,
            role_id=after.id,
            changes=changes,
            role_colour=after.colour if after.colour.value else None
        )

        try:
            await channel.send(view=view)
        except discord.Forbidden:
            logger.warning(f"ログ送信権限なし: guild_id={after.guild.id}")
