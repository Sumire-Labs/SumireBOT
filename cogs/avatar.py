"""
Avatar コマンド Cog
Components V2 を使用
"""
from __future__ import annotations

import discord
from discord import app_commands, ui
from discord.ext import commands
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

        # メインコンテナ
        container = ui.Container(accent_colour=color)

        # ヘッダー
        container.add_item(ui.TextDisplay(f"# 👤 {target.display_name} のアバター"))
        container.add_item(ui.Separator())

        # アバター画像（MediaGallery使用）
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

        self.add_item(container)

        # ダウンロードボタン（ActionRow）
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

        self.add_item(action_row)


class Avatar(commands.Cog):
    """Avatarコマンド"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.config = Config()

    @app_commands.command(name="avatar", description="ユーザーのアバターを表示します")
    @app_commands.describe(user="アバターを表示するユーザー（省略で自分）")
    async def avatar(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.User] = None
    ) -> None:
        """ユーザーのアバターとバナーを表示するコマンド"""
        await interaction.response.defer()

        target = user or interaction.user

        # ユーザー情報を取得（バナー取得のため）
        try:
            fetched_user = await self.bot.fetch_user(target.id)
        except discord.NotFound:
            fetched_user = target

        # アバターURL
        avatar_url = target.display_avatar.url
        global_avatar_url = target.avatar.url if target.avatar else None

        # サーバー固有アバター（メンバーの場合）
        server_avatar_url = None
        if isinstance(target, discord.Member) and target.guild_avatar:
            server_avatar_url = target.guild_avatar.url

        # バナーURL
        banner_url = fetched_user.banner.url if fetched_user.banner else None

        # Components V2 Viewを作成
        view = AvatarView(
            target=target,
            avatar_url=avatar_url,
            global_avatar_url=global_avatar_url,
            server_avatar_url=server_avatar_url,
            banner_url=banner_url,
            accent_color=fetched_user.accent_color
        )

        await interaction.followup.send(view=view)


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(Avatar(bot))
