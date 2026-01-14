"""
Avatar コマンド Cog
"""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from utils.config import Config
from utils.embeds import EmbedBuilder


class AvatarDownloadView(discord.ui.View):
    """アバターダウンロードボタン用View"""

    def __init__(self, avatar_url: str, banner_url: Optional[str] = None) -> None:
        super().__init__(timeout=300)

        # アバターダウンロードボタン
        self.add_item(
            discord.ui.Button(
                label="アバターをダウンロード",
                style=discord.ButtonStyle.link,
                url=avatar_url,
                emoji="📥"
            )
        )

        # バナーダウンロードボタン（存在する場合）
        if banner_url:
            self.add_item(
                discord.ui.Button(
                    label="バナーをダウンロード",
                    style=discord.ButtonStyle.link,
                    url=banner_url,
                    emoji="🖼️"
                )
            )


class Avatar(commands.Cog):
    """Avatarコマンド"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.config = Config()
        self.embed_builder = EmbedBuilder()

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

        # メインEmbed
        embed = self.embed_builder.create(
            title=f"{target.display_name} のアバター",
            color=target.accent_color or self.config.embed_color
        )

        embed.set_image(url=avatar_url)
        embed.set_author(name=str(target), icon_url=avatar_url)

        # アバター情報
        avatar_info = []
        if server_avatar_url:
            avatar_info.append(f"🏠 [サーバーアバター]({server_avatar_url})")
        if global_avatar_url:
            avatar_info.append(f"🌐 [グローバルアバター]({global_avatar_url})")
        if banner_url:
            avatar_info.append(f"🖼️ [バナー]({banner_url})")

        if avatar_info:
            embed.add_field(
                name="リンク",
                value="\n".join(avatar_info),
                inline=False
            )

        embed.set_footer(text=f"ユーザーID: {target.id}")

        # ダウンロードボタン
        view = AvatarDownloadView(
            avatar_url=avatar_url,
            banner_url=banner_url
        )

        await interaction.followup.send(embed=embed, view=view)


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(Avatar(bot))
