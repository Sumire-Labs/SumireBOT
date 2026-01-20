"""
チケット設定コマンド
"""
from __future__ import annotations

import discord
from discord import app_commands, ui

from utils.checks import Checks
from utils.logging import get_logger
from views.ticket_views import TicketPanelView
from views.persistent import PersistentViewManager
from views.common_views import CommonErrorView, CommonWarningView

logger = get_logger("sumire.cogs.ticket")


class TicketSetupSuccessView(ui.LayoutView):
    """チケットセットアップ成功View"""

    def __init__(self, panel_url: str, category_mention: str) -> None:
        super().__init__(timeout=300)

        container = ui.Container(accent_colour=discord.Colour.green())

        container.add_item(ui.TextDisplay("# ✅ チケットシステムを設定しました"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay("チケットパネルを設置しました。"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(
            f"**パネル:** [パネルへジャンプ]({panel_url})\n"
            f"**カテゴリ:** {category_mention}"
        ))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(
            "**📋 使い方**\n"
            "ユーザーがパネルのボタンをクリックすると、\n"
            "自動的にチケットチャンネルが作成されます。"
        ))

        self.add_item(container)


class TicketMixin:
    """チケットコマンド Mixin"""

    @app_commands.command(name="ticket", description="チケットパネルを設置します")
    @app_commands.default_permissions(administrator=True)
    @Checks.is_admin()
    async def ticket_setup(self, interaction: discord.Interaction) -> None:
        """チケットシステムをセットアップするコマンド"""
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        channel = interaction.channel

        # 既存の設定をチェック
        existing = await self.db.get_ticket_settings(guild.id)
        if existing and existing.get("panel_message_id"):
            try:
                old_channel = guild.get_channel(existing["panel_channel_id"])
                if old_channel:
                    old_message = await old_channel.fetch_message(existing["panel_message_id"])
                    if old_message:
                        view = CommonWarningView(
                            title="既存のパネルがあります",
                            description=f"既にチケットパネルが設置されています。\n"
                                       f"{old_channel.mention}\n\n"
                                       f"新しいパネルを設置するには、先に既存のパネルを削除してください。"
                        )
                        await interaction.followup.send(view=view)
                        return
            except discord.NotFound:
                pass

        # チケット用カテゴリを作成または取得
        category_name = "📫 チケット"
        category = discord.utils.get(guild.categories, name=category_name)

        if not category:
            try:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    guild.me: discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        manage_channels=True,
                        manage_permissions=True
                    )
                }
                category = await guild.create_category(
                    name=category_name,
                    overwrites=overwrites,
                    reason="チケットシステムセットアップ"
                )
                logger.info(f"チケットカテゴリ作成: {category.name} in {guild.name}")
            except discord.Forbidden:
                view = CommonErrorView(
                    title="権限エラー",
                    description="カテゴリを作成する権限がありません。"
                )
                await interaction.followup.send(view=view)
                return

        # チケットパネルを送信
        panel_view = TicketPanelView(self.bot)

        try:
            panel_message = await channel.send(view=panel_view)
        except discord.Forbidden:
            view = CommonErrorView(
                title="権限エラー",
                description="メッセージを送信する権限がありません。"
            )
            await interaction.followup.send(view=view)
            return

        # 設定を保存
        await self.db.setup_ticket_system(
            guild_id=guild.id,
            category_id=category.id,
            panel_channel_id=channel.id,
            panel_message_id=panel_message.id
        )

        # 永続的Viewとして保存
        await PersistentViewManager.save_view(
            guild_id=guild.id,
            channel_id=channel.id,
            message_id=panel_message.id,
            view_type="ticket_panel"
        )

        # 完了メッセージ
        view = TicketSetupSuccessView(
            panel_url=panel_message.jump_url,
            category_mention=category.mention
        )
        await interaction.followup.send(view=view)
        logger.info(f"チケットシステムセットアップ完了: guild={guild.name}")
