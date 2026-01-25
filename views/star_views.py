"""
スター評価用 Components V2 View
"""
from __future__ import annotations

from typing import Optional
from datetime import datetime

import discord
from discord import ui

from utils.database import Database
from utils.config import Config
from utils.logging import get_logger

logger = get_logger("sumire.views.star")


class StarSettingsView(ui.LayoutView):
    """スター評価設定パネル"""

    def __init__(
        self,
        guild: discord.Guild,
        enabled: bool = True,
        target_channels: list[int] = None,
        weekly_report_channel_id: Optional[int] = None
    ) -> None:
        super().__init__(timeout=300)
        self.guild = guild
        self.db = Database()
        self.config = Config()
        self.enabled = enabled
        self.target_channels = target_channels or []
        self.weekly_report_channel_id = weekly_report_channel_id

        self._build_ui()

    def _build_ui(self) -> None:
        """UIを構築"""
        container = ui.Container(accent_colour=discord.Colour.gold())

        container.add_item(ui.TextDisplay("# ⭐ スター評価設定"))
        container.add_item(ui.Separator())

        status_emoji = "🟢" if self.enabled else "🔴"
        status_text = "有効" if self.enabled else "無効"
        container.add_item(ui.TextDisplay(f"**ステータス:** {status_emoji} {status_text}"))

        if self.target_channels:
            channels_text = "\n".join([f"• <#{ch}>" for ch in self.target_channels[:10]])
            if len(self.target_channels) > 10:
                channels_text += f"\n... 他 {len(self.target_channels) - 10} チャンネル"
            container.add_item(ui.TextDisplay(f"**対象チャンネル:**\n{channels_text}"))
        else:
            container.add_item(ui.TextDisplay("**対象チャンネル:** なし"))

        # 週間レポート設定
        if self.weekly_report_channel_id:
            container.add_item(ui.TextDisplay(f"**週間レポート:** <#{self.weekly_report_channel_id}>"))
        else:
            container.add_item(ui.TextDisplay("**週間レポート:** 無効"))

        container.add_item(ui.Separator())

        toggle_row = ui.ActionRow()
        if self.enabled:
            toggle_row.add_item(ui.Button(
                label="無効にする",
                style=discord.ButtonStyle.danger,
                custom_id="star:settings:disable"
            ))
        else:
            toggle_row.add_item(ui.Button(
                label="有効にする",
                style=discord.ButtonStyle.success,
                custom_id="star:settings:enable"
            ))
        container.add_item(toggle_row)

        channel_row = ui.ActionRow()
        channel_select = ui.ChannelSelect(
            placeholder="対象チャンネルを選択...",
            channel_types=[discord.ChannelType.text],
            custom_id="star:settings:channel"
        )
        channel_row.add_item(channel_select)
        container.add_item(channel_row)

        # 週間レポートチャンネル選択
        weekly_row = ui.ActionRow()
        weekly_select = ui.ChannelSelect(
            placeholder="週間レポート送信先を選択...",
            channel_types=[discord.ChannelType.text],
            custom_id="star:settings:weekly_channel"
        )
        weekly_row.add_item(weekly_select)
        container.add_item(weekly_row)

        # ボタン行
        button_row = ui.ActionRow()
        if self.target_channels:
            button_row.add_item(ui.Button(
                label="対象をすべて解除",
                style=discord.ButtonStyle.secondary,
                custom_id="star:settings:clear"
            ))
        if self.weekly_report_channel_id:
            button_row.add_item(ui.Button(
                label="週間レポート解除",
                style=discord.ButtonStyle.secondary,
                custom_id="star:settings:weekly_clear"
            ))
        if button_row.children:
            container.add_item(button_row)

        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """インタラクションのチェックとルーティング"""
        custom_id = interaction.data.get("custom_id", "")

        if custom_id == "star:settings:enable":
            await self._toggle_enabled(interaction, True)
            return False
        elif custom_id == "star:settings:disable":
            await self._toggle_enabled(interaction, False)
            return False
        elif custom_id == "star:settings:channel":
            await self._toggle_channel(interaction)
            return False
        elif custom_id == "star:settings:clear":
            await self._clear_channels(interaction)
            return False
        elif custom_id == "star:settings:weekly_channel":
            await self._set_weekly_channel(interaction)
            return False
        elif custom_id == "star:settings:weekly_clear":
            await self._clear_weekly_channel(interaction)
            return False

        return True

    async def _toggle_enabled(self, interaction: discord.Interaction, enabled: bool) -> None:
        """有効/無効を切り替え"""
        await interaction.response.defer()
        await self.db.set_star_enabled(self.guild.id, enabled)
        self.enabled = enabled

        self.clear_items()
        self._build_ui()
        await interaction.edit_original_response(view=self)

        status = "有効" if enabled else "無効"
        logger.info(f"スター評価{status}化: {self.guild.name}")

    async def _toggle_channel(self, interaction: discord.Interaction) -> None:
        """チャンネルの対象を切り替え"""
        await interaction.response.defer()

        selected_channels = interaction.data.get("values", [])
        if not selected_channels:
            return

        channel_id = int(selected_channels[0])

        if channel_id in self.target_channels:
            await self.db.remove_star_channel(self.guild.id, channel_id)
            self.target_channels.remove(channel_id)
        else:
            await self.db.add_star_channel(self.guild.id, channel_id)
            self.target_channels.append(channel_id)

        self.clear_items()
        self._build_ui()
        await interaction.edit_original_response(view=self)

    async def _clear_channels(self, interaction: discord.Interaction) -> None:
        """すべての対象チャンネルを解除"""
        await interaction.response.defer()
        await self.db.clear_star_channels(self.guild.id)
        self.target_channels = []

        self.clear_items()
        self._build_ui()
        await interaction.edit_original_response(view=self)

    async def _set_weekly_channel(self, interaction: discord.Interaction) -> None:
        """週間レポートチャンネルを設定"""
        await interaction.response.defer()

        selected_channels = interaction.data.get("values", [])
        if not selected_channels:
            return

        channel_id = int(selected_channels[0])
        await self.db.set_weekly_report_channel(self.guild.id, channel_id)
        self.weekly_report_channel_id = channel_id

        self.clear_items()
        self._build_ui()
        await interaction.edit_original_response(view=self)

        logger.info(f"週間レポートチャンネル設定: {self.guild.name} -> {channel_id}")

    async def _clear_weekly_channel(self, interaction: discord.Interaction) -> None:
        """週間レポートチャンネルを解除"""
        await interaction.response.defer()
        await self.db.set_weekly_report_channel(self.guild.id, None)
        self.weekly_report_channel_id = None

        self.clear_items()
        self._build_ui()
        await interaction.edit_original_response(view=self)

        logger.info(f"週間レポートチャンネル解除: {self.guild.name}")


class StarLeaderboardView(ui.LayoutView):
    """スターランキング表示View"""

    def __init__(
        self,
        guild: discord.Guild,
        message_rankings: list[dict],
        author_rankings: list[dict],
        period: str = "weekly"
    ) -> None:
        super().__init__(timeout=300)

        period_names = {
            "weekly": "週間",
            "monthly": "月間",
            "all": "全期間"
        }
        period_name = period_names.get(period, "週間")

        container = ui.Container(accent_colour=discord.Colour.gold())

        # ヘッダー
        container.add_item(ui.TextDisplay(f"# 🌟 スターボード - {period_name}ランキング"))
        container.add_item(ui.Separator())

        # 投稿ランキング
        medals = ["🥇", "🥈", "🥉"]
        if message_rankings:
            msg_text = ""
            for idx, data in enumerate(message_rankings, 1):
                medal = medals[idx - 1] if idx <= 3 else f"**{idx}.**"
                message_link = f"https://discord.com/channels/{guild.id}/{data['channel_id']}/{data['message_id']}"
                msg_text += f"{medal} ⭐{data['star_count']} - [投稿を見る]({message_link}) by <@{data['author_id']}>\n"
            container.add_item(ui.TextDisplay(f"### 📸 投稿ランキング\n{msg_text}"))
        else:
            container.add_item(ui.TextDisplay("### 📸 投稿ランキング\nデータがありません"))

        container.add_item(ui.Separator())

        # 投稿者ランキング
        if author_rankings:
            author_text = ""
            for idx, data in enumerate(author_rankings, 1):
                medal = medals[idx - 1] if idx <= 3 else f"**{idx}.**"
                author_text += f"{medal} <@{data['author_id']}> - ⭐{data['total_stars']} ({data['post_count']}投稿)\n"
            container.add_item(ui.TextDisplay(f"### 👤 投稿者ランキング\n{author_text}"))
        else:
            container.add_item(ui.TextDisplay("### 👤 投稿者ランキング\nデータがありません"))

        self.add_item(container)


class StarInfoView(ui.LayoutView):
    """個別メッセージのスター情報View"""

    def __init__(
        self,
        guild: discord.Guild,
        star_data: dict,
        message_preview: Optional[str] = None
    ) -> None:
        super().__init__(timeout=300)

        container = ui.Container(accent_colour=discord.Colour.gold())

        container.add_item(ui.TextDisplay("# ⭐ スター情報"))
        container.add_item(ui.Separator())

        # メッセージ情報
        message_link = f"https://discord.com/channels/{guild.id}/{star_data['channel_id']}/{star_data['message_id']}"
        created_at = datetime.fromisoformat(star_data["created_at"])
        created_timestamp = int(created_at.timestamp())

        info_text = (
            f"**投稿者:** <@{star_data['author_id']}>\n"
            f"**チャンネル:** <#{star_data['channel_id']}>\n"
            f"**スター数:** ⭐ {star_data['star_count']}\n"
            f"**投稿日時:** <t:{created_timestamp}:f>\n"
            f"**リンク:** [メッセージを見る]({message_link})"
        )
        container.add_item(ui.TextDisplay(info_text))

        if message_preview:
            container.add_item(ui.Separator())
            preview = message_preview[:200] + "..." if len(message_preview) > 200 else message_preview
            container.add_item(ui.TextDisplay(f"**プレビュー:**\n> {preview}"))

        self.add_item(container)
