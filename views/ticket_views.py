"""
チケットシステム用View
Components V2 (LayoutView + Container) を使用
"""
from __future__ import annotations

import discord
from discord import ui
from typing import TYPE_CHECKING, Optional

from utils.config import Config
from utils.database import Database
from utils.logging import get_logger
from views.common_views import (
    CommonErrorView,
    CommonSuccessView,
    CommonInfoView,
    CommonWarningView
)

if TYPE_CHECKING:
    from bot import SumireBot

logger = get_logger("sumire.views.ticket")


class TicketWelcomeView(ui.LayoutView):
    """チケットウェルカムメッセージ用View"""

    def __init__(self, ticket_number: int, user: discord.Member) -> None:
        super().__init__(timeout=300)

        container = ui.Container(accent_colour=discord.Colour.purple())

        container.add_item(ui.TextDisplay(f"# 🎫 チケット #{ticket_number:03d}"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(
            f"{user.mention} さん、チケットを作成していただきありがとうございます。\n\n"
            f"お問い合わせ内容をこちらにご記入ください。\n"
            f"スタッフが対応いたします。"
        ))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(
            f"**作成者:** {user.mention}\n"
            f"**ステータス:** 🟢 オープン"
        ))

        self.add_item(container)


class TicketPanelView(ui.LayoutView):
    """
    チケット作成パネル
    Components V2 (LayoutView + Container) を使用
    """

    def __init__(self, bot: Optional[SumireBot] = None) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.config = Config()
        self.db = Database()

        # Container を作成
        container = ui.Container(accent_colour=discord.Colour.purple())

        # ヘッダーセクション（Thumbnailをaccessoryとして使用）
        header_section = ui.Section(
            ui.TextDisplay("# 🎫 サポートチケット"),
            ui.TextDisplay(
                "サポートが必要な場合は、下のボタンをクリックして\n"
                "チケットを作成してください。スタッフが対応いたします。"
            ),
            accessory=ui.Thumbnail("https://cdn.discordapp.com/embed/avatars/0.png")
        )
        container.add_item(header_section)

        # 区切り線
        container.add_item(ui.Separator())

        # 注意事項テキスト
        container.add_item(ui.TextDisplay(
            "📋 **チケット作成時の注意:**\n"
            "• お問い合わせ内容を明確にご記入ください\n"
            "• 同時に複数のチケットを作成しないでください\n"
            "• スタッフの返信をお待ちください"
        ))

        # 区切り線
        container.add_item(ui.Separator())

        # ボタン用ActionRow
        action_row = ui.ActionRow()
        create_button = ui.Button(
            label="🎫 チケットを作成",
            style=discord.ButtonStyle.primary,
            custom_id="ticket:panel:create"
        )
        action_row.add_item(create_button)
        container.add_item(action_row)

        # ContainerをLayoutViewに追加
        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """インタラクションのチェックとルーティング"""
        if interaction.data.get("custom_id") == "ticket:panel:create":
            await self.create_ticket(interaction)
            return False
        return True

    async def create_ticket(self, interaction: discord.Interaction) -> None:
        """チケット作成処理"""
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        user = interaction.user

        # チケット設定を取得
        settings = await self.db.get_ticket_settings(guild.id)
        if not settings or not settings.get("category_id"):
            view = CommonErrorView(
                title="設定エラー",
                description="チケットシステムが正しく設定されていません。"
            )
            await interaction.followup.send(view=view, ephemeral=True)
            return

        # カテゴリを取得
        category = guild.get_channel(settings["category_id"])
        if not category:
            view = CommonErrorView(
                title="設定エラー",
                description="チケットカテゴリが見つかりません。"
            )
            await interaction.followup.send(view=view, ephemeral=True)
            return

        # チケット番号を取得
        ticket_number = await self.db.get_next_ticket_number(guild.id)

        # チケットチャンネルを作成
        prefix = self.config.ticket_channel_prefix
        channel_name = f"{prefix}-{ticket_number:03d}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
                manage_messages=True
            )
        }

        try:
            channel = await category.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                reason=f"チケット作成: {user}"
            )
        except discord.Forbidden:
            view = CommonErrorView(
                title="権限エラー",
                description="チャンネルを作成する権限がありません。"
            )
            await interaction.followup.send(view=view, ephemeral=True)
            return
        except Exception as e:
            logger.error(f"チケットチャンネル作成エラー: {e}")
            view = CommonErrorView(
                title="エラー",
                description="チケットの作成中にエラーが発生しました。"
            )
            await interaction.followup.send(view=view, ephemeral=True)
            return

        # データベースにチケットを保存
        ticket_id = await self.db.create_ticket(
            guild_id=guild.id,
            channel_id=channel.id,
            user_id=user.id,
            ticket_number=ticket_number
        )

        # チケット制御パネルを送信
        control_view = TicketControlView(self.bot, ticket_id)
        control_message = await channel.send(view=control_view)

        # 永続的Viewとして保存
        from .persistent import PersistentViewManager
        await PersistentViewManager.save_view(
            guild_id=guild.id,
            channel_id=channel.id,
            message_id=control_message.id,
            view_type="ticket_control",
            data={"ticket_id": ticket_id}
        )

        # ウェルカムメッセージ
        welcome_view = TicketWelcomeView(ticket_number=ticket_number, user=user)
        await channel.send(content=user.mention, view=welcome_view)

        # 完了メッセージ
        success_view = CommonSuccessView(
            title="チケットを作成しました",
            description=f"{channel.mention}"
        )
        await interaction.followup.send(view=success_view, ephemeral=True)

        logger.info(f"チケット作成: #{ticket_number:03d} by {user} in {guild.name}")


class TicketControlView(ui.LayoutView):
    """
    チケット制御パネル
    Components V2 (LayoutView + Container) を使用
    """

    def __init__(self, bot: Optional[SumireBot] = None, ticket_id: int = 0) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.ticket_id = ticket_id
        self.db = Database()
        self.config = Config()

        # Container を作成
        container = ui.Container(accent_colour=discord.Colour.blue())

        # ヘッダー
        container.add_item(ui.TextDisplay("# ⚙️ チケット管理パネル"))
        container.add_item(ui.TextDisplay("下のボタンやメニューでチケットを管理できます。"))
        container.add_item(ui.Separator())

        # カテゴリ選択用ActionRow
        category_row = ui.ActionRow()
        category_select = ui.Select(
            placeholder="📋 カテゴリを選択...",
            options=[
                discord.SelectOption(label=cat, value=cat)
                for cat in self.config.ticket_categories
            ],
            custom_id=f"ticket:control:category:{ticket_id}"
        )
        category_row.add_item(category_select)
        container.add_item(category_row)

        # ボタン用ActionRow
        button_row = ui.ActionRow()
        button_row.add_item(ui.Button(
            label="⏸️ 保留",
            style=discord.ButtonStyle.secondary,
            custom_id="ticket:control:hold"
        ))
        button_row.add_item(ui.Button(
            label="👤 担当者追加",
            style=discord.ButtonStyle.secondary,
            custom_id="ticket:control:assign"
        ))
        button_row.add_item(ui.Button(
            label="🔒 クローズ",
            style=discord.ButtonStyle.danger,
            custom_id="ticket:control:close"
        ))
        container.add_item(button_row)

        # ContainerをLayoutViewに追加
        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """インタラクションのチェックとルーティング"""
        custom_id = interaction.data.get("custom_id", "")

        if custom_id == "ticket:control:hold":
            await self.hold_ticket(interaction)
            return False
        elif custom_id == "ticket:control:assign":
            await self.assign_staff(interaction)
            return False
        elif custom_id == "ticket:control:close":
            await self.close_ticket(interaction)
            return False
        elif custom_id.startswith("ticket:control:category:"):
            await self.set_category(interaction)
            return False

        return True

    async def hold_ticket(self, interaction: discord.Interaction) -> None:
        """チケットを保留状態に"""
        await interaction.response.defer(ephemeral=True)

        ticket = await self.db.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            return

        new_status = "open" if ticket["status"] == "on_hold" else "on_hold"
        await self.db.update_ticket_status(interaction.channel.id, new_status)

        status_text = "🟡 保留中" if new_status == "on_hold" else "🟢 オープン"
        view = CommonInfoView(
            title="ステータス変更",
            description=f"チケットのステータスを **{status_text}** に変更しました。"
        )
        await interaction.followup.send(view=view, ephemeral=True)

        # チャンネル名を更新
        try:
            prefix = self.config.ticket_channel_prefix
            if new_status == "on_hold":
                await interaction.channel.edit(name=f"hold-{ticket['ticket_number']:03d}")
            else:
                await interaction.channel.edit(name=f"{prefix}-{ticket['ticket_number']:03d}")
        except discord.Forbidden:
            pass

    async def assign_staff(self, interaction: discord.Interaction) -> None:
        """担当者追加モーダルを表示"""
        modal = AssignStaffModal(interaction.channel)
        await interaction.response.send_modal(modal)

    async def close_ticket(self, interaction: discord.Interaction) -> None:
        """チケットをクローズ"""
        await interaction.response.defer(ephemeral=True)

        # 確認View
        confirm_view = ConfirmCloseView(interaction.channel.id)
        await interaction.followup.send(view=confirm_view, ephemeral=True)

    async def set_category(self, interaction: discord.Interaction) -> None:
        """カテゴリを設定"""
        await interaction.response.defer(ephemeral=True)

        selected = interaction.data.get("values", [None])[0]
        if not selected:
            return

        await self.db.update_ticket_category(interaction.channel.id, selected)

        view = CommonSuccessView(
            title="カテゴリを設定しました",
            description=f"カテゴリ: **{selected}**"
        )
        await interaction.followup.send(view=view, ephemeral=True)

        logger.info(f"チケットカテゴリ変更: {selected} - channel_id={interaction.channel.id}")


class AssignStaffModal(ui.Modal, title="担当者追加"):
    """担当者追加用モーダル"""

    user_id = ui.TextInput(
        label="ユーザーID または @メンション",
        placeholder="例: 123456789 または @User",
        required=True
    )

    def __init__(self, channel: discord.TextChannel) -> None:
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """モーダル送信時"""
        await interaction.response.defer(ephemeral=True)

        input_value = self.user_id.value.strip()

        # メンションからIDを抽出
        if input_value.startswith("<@") and input_value.endswith(">"):
            input_value = input_value[2:-1]
            if input_value.startswith("!"):
                input_value = input_value[1:]

        try:
            user_id = int(input_value)
            member = interaction.guild.get_member(user_id)
        except ValueError:
            view = CommonErrorView(
                title="無効な入力",
                description="有効なユーザーIDを入力してください。"
            )
            await interaction.followup.send(view=view, ephemeral=True)
            return

        if not member:
            view = CommonErrorView(
                title="ユーザーが見つかりません",
                description="指定されたユーザーはこのサーバーにいません。"
            )
            await interaction.followup.send(view=view, ephemeral=True)
            return

        # チャンネルの権限を追加
        try:
            await self.channel.set_permissions(
                member,
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )

            view = CommonSuccessView(
                title="担当者を追加しました",
                description=f"{member.mention} をチケットに追加しました。"
            )
            await interaction.followup.send(view=view, ephemeral=True)

            # チャンネルに通知
            notify_view = CommonInfoView(
                title="担当者追加",
                description=f"{member.mention} がチケットに追加されました。"
            )
            await self.channel.send(view=notify_view)

            logger.info(f"担当者追加: {member} to channel_id={self.channel.id}")

        except discord.Forbidden:
            view = CommonErrorView(
                title="権限エラー",
                description="ユーザーを追加する権限がありません。"
            )
            await interaction.followup.send(view=view, ephemeral=True)


class ConfirmCloseView(ui.LayoutView):
    """チケットクローズ確認View (Components V2)"""

    def __init__(self, channel_id: int) -> None:
        super().__init__(timeout=60)
        self.channel_id = channel_id
        self.db = Database()

        container = ui.Container(accent_colour=discord.Colour.orange())

        container.add_item(ui.TextDisplay("# ⚠️ チケットをクローズしますか？"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(
            "この操作はチケットチャンネルを削除します。\n"
            "本当にクローズしますか？"
        ))
        container.add_item(ui.Separator())

        button_row = ui.ActionRow()
        button_row.add_item(ui.Button(
            label="✅ はい、クローズします",
            style=discord.ButtonStyle.danger,
            custom_id="ticket:close:confirm"
        ))
        button_row.add_item(ui.Button(
            label="❌ キャンセル",
            style=discord.ButtonStyle.secondary,
            custom_id="ticket:close:cancel"
        ))
        container.add_item(button_row)

        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """インタラクションのチェックとルーティング"""
        custom_id = interaction.data.get("custom_id", "")

        if custom_id == "ticket:close:confirm":
            await self._confirm_close(interaction)
            return False
        elif custom_id == "ticket:close:cancel":
            await interaction.response.defer()
            await interaction.delete_original_response()
            return False

        return True

    async def _confirm_close(self, interaction: discord.Interaction) -> None:
        """クローズ確認"""
        await interaction.response.defer()

        # ステータスを更新
        await self.db.update_ticket_status(self.channel_id, "closed")

        view = CommonInfoView(
            title="チケットをクローズしています...",
            description="5秒後にこのチャンネルは削除されます。"
        )
        await interaction.followup.send(view=view)

        # 5秒待ってからチャンネル削除
        import asyncio
        await asyncio.sleep(5)

        channel = interaction.channel
        if channel:
            try:
                await channel.delete(reason="チケットクローズ")
                logger.info(f"チケットチャンネル削除: {channel.name}")
            except discord.Forbidden:
                logger.error(f"チャンネル削除権限なし: {channel.name}")
