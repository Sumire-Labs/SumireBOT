"""
コンテキストメニュー（右クリック→アプリ）コマンド
"""
from __future__ import annotations

import discord
from discord import app_commands, ui

from utils.logging import get_logger
from views.common_views import CommonSuccessView, CommonErrorView

logger = get_logger("sumire.cogs.utility.context_menus")


class BookmarkView(ui.LayoutView):
    """ブックマーク用 View"""

    def __init__(
        self,
        message: discord.Message,
        guild_name: str
    ) -> None:
        super().__init__(timeout=None)

        container = ui.Container(accent_colour=discord.Colour.gold())

        # ヘッダー
        container.add_item(ui.TextDisplay("# 📌 ブックマーク"))
        container.add_item(ui.Separator())

        # サーバー/チャンネル情報
        container.add_item(ui.TextDisplay(
            f"**サーバー:** {guild_name}\n"
            f"**チャンネル:** #{message.channel.name}\n"
            f"**投稿者:** {message.author.display_name}"
        ))
        container.add_item(ui.Separator())

        # メッセージ内容
        if message.content:
            # 長すぎる場合は切り詰め
            content = message.content
            if len(content) > 1500:
                content = content[:1500] + "..."
            container.add_item(ui.TextDisplay(content))
        else:
            container.add_item(ui.TextDisplay("-# （テキストなし）"))

        # 添付ファイル
        if message.attachments:
            attachment_text = "\n".join(
                f"📎 [{a.filename}]({a.url})" for a in message.attachments[:5]
            )
            container.add_item(ui.Separator())
            container.add_item(ui.TextDisplay(f"**添付ファイル:**\n{attachment_text}"))

        container.add_item(ui.Separator())

        # リンクボタン
        action_row = ui.ActionRow()
        action_row.add_item(ui.Button(
            label="元のメッセージへ",
            style=discord.ButtonStyle.link,
            url=message.jump_url,
            emoji="🔗"
        ))
        container.add_item(action_row)

        self.add_item(container)


class ContextMenusMixin:
    """コンテキストメニューコマンド Mixin"""

    # ==================== メッセージコンテキストメニュー ====================

    @app_commands.context_menu(name="📌 ブックマーク")
    async def bookmark_message(
        self,
        interaction: discord.Interaction,
        message: discord.Message
    ) -> None:
        """メッセージをDMにブックマーク"""
        try:
            # DMに送信
            view = BookmarkView(
                message=message,
                guild_name=interaction.guild.name if interaction.guild else "DM"
            )
            await interaction.user.send(view=view)

            # 確認メッセージ
            success_view = CommonSuccessView(
                title="ブックマーク完了",
                description="メッセージをDMに保存しました。"
            )
            await interaction.response.send_message(view=success_view, ephemeral=True)

            logger.debug(f"ブックマーク: {interaction.user} -> message {message.id}")

        except discord.Forbidden:
            error_view = CommonErrorView(
                title="エラー",
                description="DMを送信できませんでした。\nDMの受信設定を確認してください。"
            )
            await interaction.response.send_message(view=error_view, ephemeral=True)

    @app_commands.context_menu(name="🔗 リンクを取得")
    async def get_message_link(
        self,
        interaction: discord.Interaction,
        message: discord.Message
    ) -> None:
        """メッセージのリンクを取得"""
        await interaction.response.send_message(
            f"```\n{message.jump_url}\n```",
            ephemeral=True
        )

    # ==================== ユーザーコンテキストメニュー ====================

    @app_commands.context_menu(name="👤 プロフィール")
    async def user_profile(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ) -> None:
        """ユーザーのプロフィールを表示"""
        if not interaction.guild:
            view = CommonErrorView(
                title="エラー",
                description="サーバー内でのみ使用できます。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        from utils.database import Database
        from views.profile_views import ProfileView

        db = Database()
        user_data = await db.get_user_level(interaction.guild.id, user.id)

        vc_time = 0
        reactions_given = 0
        reactions_received = 0

        if user_data:
            vc_time = user_data.get("vc_time", 0)
            reactions_given = user_data.get("reactions_given", 0)
            reactions_received = user_data.get("reactions_received", 0)

        view = ProfileView(
            member=user,
            vc_time=vc_time,
            reactions_given=reactions_given,
            reactions_received=reactions_received
        )

        await interaction.followup.send(view=view, ephemeral=True)

    @app_commands.context_menu(name="🖼️ アバター")
    async def user_avatar(
        self,
        interaction: discord.Interaction,
        user: discord.User
    ) -> None:
        """ユーザーのアバターを表示"""
        await interaction.response.defer(ephemeral=True)

        from cogs.general.avatar import AvatarView

        try:
            fetched_user = await self.bot.fetch_user(user.id)
        except discord.NotFound:
            fetched_user = user

        avatar_url = user.display_avatar.url
        global_avatar_url = user.avatar.url if user.avatar else None

        server_avatar_url = None
        if isinstance(user, discord.Member) and user.guild_avatar:
            server_avatar_url = user.guild_avatar.url

        banner_url = fetched_user.banner.url if fetched_user.banner else None

        view = AvatarView(
            target=user,
            avatar_url=avatar_url,
            global_avatar_url=global_avatar_url,
            server_avatar_url=server_avatar_url,
            banner_url=banner_url,
            accent_color=fetched_user.accent_color
        )

        await interaction.followup.send(view=view, ephemeral=True)
