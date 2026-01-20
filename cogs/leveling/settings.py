"""
Leveling 設定コマンド
"""
from __future__ import annotations

import discord
from discord import app_commands, ui

from utils.config import Config
from utils.database import Database
from utils.checks import Checks
from utils.logging import get_logger
from views.common_views import CommonErrorView

logger = get_logger("sumire.cogs.leveling.settings")


class LevelingSettingsView(ui.LayoutView):
    """レベルシステム設定パネル"""

    def __init__(
        self,
        guild: discord.Guild,
        enabled: bool = True,
        ignored_channels: list[int] = None
    ) -> None:
        super().__init__(timeout=300)
        self.guild = guild
        self.db = Database()
        self.config = Config()
        self.enabled = enabled
        self.ignored_channels = ignored_channels or []

        self._build_ui()

    def _build_ui(self) -> None:
        """UIを構築"""
        container = ui.Container(accent_colour=discord.Colour.gold())

        container.add_item(ui.TextDisplay("# 📊 レベルシステム設定"))
        container.add_item(ui.Separator())

        status_emoji = "🟢" if self.enabled else "🔴"
        status_text = "有効" if self.enabled else "無効"
        container.add_item(ui.TextDisplay(f"**ステータス:** {status_emoji} {status_text}"))

        if self.ignored_channels:
            channels_text = "\n".join([f"• <#{ch}>" for ch in self.ignored_channels[:10]])
            if len(self.ignored_channels) > 10:
                channels_text += f"\n... 他 {len(self.ignored_channels) - 10} チャンネル"
            container.add_item(ui.TextDisplay(f"**XP除外チャンネル:**\n{channels_text}"))
        else:
            container.add_item(ui.TextDisplay("**XP除外チャンネル:** なし"))

        container.add_item(ui.Separator())

        toggle_row = ui.ActionRow()
        if self.enabled:
            toggle_row.add_item(ui.Button(
                label="無効にする",
                style=discord.ButtonStyle.danger,
                custom_id="leveling:settings:disable"
            ))
        else:
            toggle_row.add_item(ui.Button(
                label="有効にする",
                style=discord.ButtonStyle.success,
                custom_id="leveling:settings:enable"
            ))
        container.add_item(toggle_row)

        channel_row = ui.ActionRow()
        channel_select = ui.ChannelSelect(
            placeholder="除外チャンネルを選択...",
            channel_types=[discord.ChannelType.text],
            custom_id="leveling:settings:channel"
        )
        channel_row.add_item(channel_select)
        container.add_item(channel_row)

        if self.ignored_channels:
            clear_row = ui.ActionRow()
            clear_row.add_item(ui.Button(
                label="除外をすべて解除",
                style=discord.ButtonStyle.secondary,
                custom_id="leveling:settings:clear"
            ))
            container.add_item(clear_row)

        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """インタラクションのチェックとルーティング"""
        custom_id = interaction.data.get("custom_id", "")

        if custom_id == "leveling:settings:enable":
            await self._toggle_enabled(interaction, True)
            return False
        elif custom_id == "leveling:settings:disable":
            await self._toggle_enabled(interaction, False)
            return False
        elif custom_id == "leveling:settings:channel":
            await self._toggle_channel(interaction)
            return False
        elif custom_id == "leveling:settings:clear":
            await self._clear_ignored(interaction)
            return False

        return True

    async def _toggle_enabled(self, interaction: discord.Interaction, enabled: bool) -> None:
        """有効/無効を切り替え"""
        await interaction.response.defer()
        await self.db.set_leveling_enabled(self.guild.id, enabled)
        self.enabled = enabled

        self.clear_items()
        self._build_ui()
        await interaction.edit_original_response(view=self)

        status = "有効" if enabled else "無効"
        logger.info(f"レベルシステム{status}化: {self.guild.name}")

    async def _toggle_channel(self, interaction: discord.Interaction) -> None:
        """チャンネルの除外を切り替え"""
        await interaction.response.defer()

        selected_channels = interaction.data.get("values", [])
        if not selected_channels:
            return

        channel_id = int(selected_channels[0])

        if channel_id in self.ignored_channels:
            await self.db.remove_ignored_channel(self.guild.id, channel_id)
            self.ignored_channels.remove(channel_id)
        else:
            await self.db.add_ignored_channel(self.guild.id, channel_id)
            self.ignored_channels.append(channel_id)

        self.clear_items()
        self._build_ui()
        await interaction.edit_original_response(view=self)

    async def _clear_ignored(self, interaction: discord.Interaction) -> None:
        """すべての除外を解除"""
        await interaction.response.defer()

        for channel_id in self.ignored_channels.copy():
            await self.db.remove_ignored_channel(self.guild.id, channel_id)

        self.ignored_channels = []

        self.clear_items()
        self._build_ui()
        await interaction.edit_original_response(view=self)


class SettingsMixin:
    """Leveling 設定コマンド Mixin"""

    @app_commands.command(name="leveling", description="レベルシステムを設定します")
    @app_commands.default_permissions(administrator=True)
    @Checks.is_admin()
    async def leveling_settings(self, interaction: discord.Interaction) -> None:
        """レベルシステム設定コマンド"""
        if not interaction.guild:
            view = CommonErrorView(
                title="エラー",
                description="このコマンドはサーバー内でのみ使用できます。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        settings = await self.db.get_leveling_settings(interaction.guild.id)
        enabled = bool(settings.get("enabled", 1)) if settings else True
        ignored_channels = settings.get("ignored_channels", []) if settings else []

        view = LevelingSettingsView(
            guild=interaction.guild,
            enabled=enabled,
            ignored_channels=ignored_channels
        )

        await interaction.response.send_message(view=view, ephemeral=True)
