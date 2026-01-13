"""
Embed生成ヘルパー
"""
from __future__ import annotations

import discord
from datetime import datetime
from typing import Optional, Union

from .config import Config


class EmbedBuilder:
    """Embedメッセージを簡単に作成するためのヘルパークラス"""

    def __init__(self) -> None:
        self.config = Config()

    def create(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[int] = None,
        timestamp: bool = True,
        footer_text: Optional[str] = None,
        footer_icon: Optional[str] = None,
        author_name: Optional[str] = None,
        author_icon: Optional[str] = None,
        author_url: Optional[str] = None,
        thumbnail: Optional[str] = None,
        image: Optional[str] = None
    ) -> discord.Embed:
        """基本的なEmbedを作成"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color or self.config.embed_color
        )

        if timestamp:
            embed.timestamp = datetime.utcnow()

        if footer_text or footer_icon:
            embed.set_footer(text=footer_text, icon_url=footer_icon)

        if author_name:
            embed.set_author(name=author_name, icon_url=author_icon, url=author_url)

        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        if image:
            embed.set_image(url=image)

        return embed

    def success(
        self,
        title: str = "成功",
        description: Optional[str] = None,
        **kwargs
    ) -> discord.Embed:
        """成功メッセージ用Embed"""
        return self.create(
            title=f"✅ {title}",
            description=description,
            color=self.config.success_color,
            **kwargs
        )

    def error(
        self,
        title: str = "エラー",
        description: Optional[str] = None,
        **kwargs
    ) -> discord.Embed:
        """エラーメッセージ用Embed"""
        return self.create(
            title=f"❌ {title}",
            description=description,
            color=self.config.error_color,
            **kwargs
        )

    def warning(
        self,
        title: str = "警告",
        description: Optional[str] = None,
        **kwargs
    ) -> discord.Embed:
        """警告メッセージ用Embed"""
        return self.create(
            title=f"⚠️ {title}",
            description=description,
            color=self.config.warning_color,
            **kwargs
        )

    def info(
        self,
        title: str = "情報",
        description: Optional[str] = None,
        **kwargs
    ) -> discord.Embed:
        """情報メッセージ用Embed"""
        return self.create(
            title=f"ℹ️ {title}",
            description=description,
            color=self.config.info_color,
            **kwargs
        )

    # ==================== ログ用Embed ====================

    def log_message_delete(
        self,
        message: discord.Message,
        content: str
    ) -> discord.Embed:
        """メッセージ削除ログ用Embed"""
        embed = self.create(
            title="📝 メッセージ削除",
            description=f"**チャンネル:** {message.channel.mention}",
            color=self.config.error_color
        )
        embed.add_field(
            name="削除されたメッセージ",
            value=content[:1024] if content else "*内容なし*",
            inline=False
        )
        embed.set_author(
            name=str(message.author),
            icon_url=message.author.display_avatar.url
        )
        embed.set_footer(text=f"ユーザーID: {message.author.id}")
        return embed

    def log_message_edit(
        self,
        before: discord.Message,
        after: discord.Message
    ) -> discord.Embed:
        """メッセージ編集ログ用Embed"""
        embed = self.create(
            title="📝 メッセージ編集",
            description=f"**チャンネル:** {after.channel.mention}\n"
                       f"[メッセージへジャンプ]({after.jump_url})",
            color=self.config.warning_color
        )
        embed.add_field(
            name="編集前",
            value=before.content[:1024] if before.content else "*内容なし*",
            inline=False
        )
        embed.add_field(
            name="編集後",
            value=after.content[:1024] if after.content else "*内容なし*",
            inline=False
        )
        embed.set_author(
            name=str(after.author),
            icon_url=after.author.display_avatar.url
        )
        embed.set_footer(text=f"ユーザーID: {after.author.id}")
        return embed

    def log_member_join(self, member: discord.Member) -> discord.Embed:
        """メンバー参加ログ用Embed"""
        embed = self.create(
            title="👤 メンバー参加",
            description=f"{member.mention} がサーバーに参加しました",
            color=self.config.success_color
        )
        embed.add_field(
            name="アカウント作成日",
            value=discord.utils.format_dt(member.created_at, "R"),
            inline=True
        )
        embed.add_field(
            name="メンバー数",
            value=str(member.guild.member_count),
            inline=True
        )
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ユーザーID: {member.id}")
        return embed

    def log_member_leave(self, member: discord.Member) -> discord.Embed:
        """メンバー退出ログ用Embed"""
        embed = self.create(
            title="👤 メンバー退出",
            description=f"{member.mention} がサーバーから退出しました",
            color=self.config.error_color
        )
        roles = [r.mention for r in member.roles if r.name != "@everyone"]
        if roles:
            embed.add_field(
                name="所持していたロール",
                value=", ".join(roles[:20]),
                inline=False
            )
        embed.add_field(
            name="参加日",
            value=discord.utils.format_dt(member.joined_at, "R") if member.joined_at else "不明",
            inline=True
        )
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ユーザーID: {member.id}")
        return embed

    def log_member_ban(
        self,
        guild: discord.Guild,
        user: Union[discord.Member, discord.User]
    ) -> discord.Embed:
        """メンバーBanログ用Embed"""
        embed = self.create(
            title="🔨 メンバーBan",
            description=f"{user.mention} がBanされました",
            color=self.config.error_color
        )
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"ユーザーID: {user.id}")
        return embed

    def log_member_unban(
        self,
        guild: discord.Guild,
        user: discord.User
    ) -> discord.Embed:
        """メンバーUnbanログ用Embed"""
        embed = self.create(
            title="🔓 メンバーUnban",
            description=f"{user.mention} のBanが解除されました",
            color=self.config.success_color
        )
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"ユーザーID: {user.id}")
        return embed

    def log_channel_create(self, channel: discord.abc.GuildChannel) -> discord.Embed:
        """チャンネル作成ログ用Embed"""
        embed = self.create(
            title="📢 チャンネル作成",
            description=f"**チャンネル:** {channel.mention}\n**タイプ:** {channel.type.name}",
            color=self.config.success_color
        )
        embed.set_footer(text=f"チャンネルID: {channel.id}")
        return embed

    def log_channel_delete(self, channel: discord.abc.GuildChannel) -> discord.Embed:
        """チャンネル削除ログ用Embed"""
        embed = self.create(
            title="📢 チャンネル削除",
            description=f"**チャンネル名:** {channel.name}\n**タイプ:** {channel.type.name}",
            color=self.config.error_color
        )
        embed.set_footer(text=f"チャンネルID: {channel.id}")
        return embed

    def log_role_create(self, role: discord.Role) -> discord.Embed:
        """ロール作成ログ用Embed"""
        embed = self.create(
            title="🎭 ロール作成",
            description=f"**ロール:** {role.mention}",
            color=role.color if role.color.value else self.config.success_color
        )
        embed.set_footer(text=f"ロールID: {role.id}")
        return embed

    def log_role_delete(self, role: discord.Role) -> discord.Embed:
        """ロール削除ログ用Embed"""
        embed = self.create(
            title="🎭 ロール削除",
            description=f"**ロール名:** {role.name}",
            color=role.color if role.color.value else self.config.error_color
        )
        embed.set_footer(text=f"ロールID: {role.id}")
        return embed
