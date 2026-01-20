"""
Avatar コマンド
"""
from __future__ import annotations

import discord
from discord import app_commands, ui
from typing import Optional

from utils.config import Config


class AvatarView(ui.LayoutView):
    """アバター表示用View (Components V2)"""

    def __init__(
        self,
        target: discord.User | discord.Member,
        avatar_url: str,
        global_avatar_url: Optional[str],
        server_avatar_url: Optional[str],
        banner_url: Optional[str],
        accent_color: Optional[discord.Colour]
    ) -> None:
        super().__init__(timeout=300)

        config = Config()
        color = accent_color or config.embed_color

        container = ui.Container(accent_colour=color)

        # ヘッダー
        container.add_item(ui.TextDisplay(f"# 👤 {target.display_name} のアバター"))
        container.add_item(ui.Separator())

        # アバター画像
        gallery = ui.MediaGallery()
        gallery.add_item(ui.MediaGalleryItem(media=avatar_url))
        container.add_item(gallery)

        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        # ユーザー情報
        info_lines = [f"**ユーザー:** {target}"]
        info_lines.append(f"**ID:** `{target.id}`")
        container.add_item(ui.TextDisplay("\n".join(info_lines)))

        # リンク情報
        link_lines = []
        if server_avatar_url:
            link_lines.append(f"🏠 [サーバーアバター]({server_avatar_url})")
        if global_avatar_url:
            link_lines.append(f"🌐 [グローバルアバター]({global_avatar_url})")
        if banner_url:
            link_lines.append(f"🖼️ [バナー]({banner_url})")

        if link_lines:
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay("**リンク:**\n" + "\n".join(link_lines)))

        container.add_item(ui.Separator())

        # ダウンロードボタン（Container内に配置）
        action_row = ui.ActionRow()
        action_row.add_item(ui.Button(
            label="アバターをダウンロード",
            style=discord.ButtonStyle.link,
            url=avatar_url,
            emoji="📥"
        ))

        if banner_url:
            action_row.add_item(ui.Button(
                label="バナーをダウンロード",
                style=discord.ButtonStyle.link,
                url=banner_url,
                emoji="🖼️"
            ))

        container.add_item(action_row)

        self.add_item(container)


class AvatarMixin:
    """Avatarコマンド Mixin"""

    @app_commands.command(name="avatar", description="ユーザーのアバターを表示します")
    @app_commands.describe(user="アバターを表示するユーザー（省略で自分）")
    async def avatar(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.User] = None
    ) -> None:
        """ユーザーのアバターとバナーを表示"""
        await interaction.response.defer()

        target = user or interaction.user

        try:
            fetched_user = await self.bot.fetch_user(target.id)
        except discord.NotFound:
            fetched_user = target

        avatar_url = target.display_avatar.url
        global_avatar_url = target.avatar.url if target.avatar else None

        server_avatar_url = None
        if isinstance(target, discord.Member) and target.guild_avatar:
            server_avatar_url = target.guild_avatar.url

        banner_url = fetched_user.banner.url if fetched_user.banner else None

        view = AvatarView(
            target=target,
            avatar_url=avatar_url,
            global_avatar_url=global_avatar_url,
            server_avatar_url=server_avatar_url,
            banner_url=banner_url,
            accent_color=fetched_user.accent_color
        )

        await interaction.followup.send(view=view)
