"""
レベルシステム Cog
メッセージ送信でXPを獲得し、レベルアップするシステム
"""
from __future__ import annotations

import random
import discord
from discord import app_commands, ui
from discord.ext import commands
from typing import TYPE_CHECKING, Optional
from datetime import datetime, timedelta

from utils.config import Config
from utils.database import Database
from utils.embeds import EmbedBuilder
from utils.logging import get_logger
from utils.checks import Checks, handle_app_command_error

if TYPE_CHECKING:
    from bot import SumireBot

logger = get_logger("sumire.cogs.leveling")

# XP設定
XP_MIN = 10
XP_MAX = 25
XP_COOLDOWN_SECONDS = 60


class LevelingSettingsView(ui.LayoutView):
    """
    レベルシステム設定パネル
    Components V2 (LayoutView + Container) を使用
    """

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
        # Container を作成
        container = ui.Container(accent_colour=discord.Colour.gold())

        # ヘッダー
        container.add_item(ui.TextDisplay("# 📊 レベルシステム設定"))
        container.add_item(ui.Separator())

        # 現在の状態
        status_emoji = "🟢" if self.enabled else "🔴"
        status_text = "有効" if self.enabled else "無効"
        container.add_item(ui.TextDisplay(f"**ステータス:** {status_emoji} {status_text}"))

        # 除外チャンネル一覧
        if self.ignored_channels:
            channels_text = "\n".join([f"• <#{ch}>" for ch in self.ignored_channels[:10]])
            if len(self.ignored_channels) > 10:
                channels_text += f"\n... 他 {len(self.ignored_channels) - 10} チャンネル"
            container.add_item(ui.TextDisplay(f"**XP除外チャンネル:**\n{channels_text}"))
        else:
            container.add_item(ui.TextDisplay("**XP除外チャンネル:** なし"))

        container.add_item(ui.Separator())

        # 有効/無効ボタン
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

        # チャンネル選択
        channel_row = ui.ActionRow()
        channel_select = ui.ChannelSelect(
            placeholder="除外チャンネルを選択...",
            channel_types=[discord.ChannelType.text],
            custom_id="leveling:settings:channel"
        )
        channel_row.add_item(channel_select)
        container.add_item(channel_row)

        # 除外解除ボタン（除外チャンネルがある場合のみ）
        if self.ignored_channels:
            clear_row = ui.ActionRow()
            clear_row.add_item(ui.Button(
                label="除外をすべて解除",
                style=discord.ButtonStyle.secondary,
                custom_id="leveling:settings:clear"
            ))
            container.add_item(clear_row)

        # ContainerをLayoutViewに追加
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

        # UIを再構築
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

        # UIを再構築
        self.clear_items()
        self._build_ui()
        await interaction.edit_original_response(view=self)

    async def _clear_ignored(self, interaction: discord.Interaction) -> None:
        """すべての除外を解除"""
        await interaction.response.defer()

        for channel_id in self.ignored_channels.copy():
            await self.db.remove_ignored_channel(self.guild.id, channel_id)

        self.ignored_channels = []

        # UIを再構築
        self.clear_items()
        self._build_ui()
        await interaction.edit_original_response(view=self)


class Leveling(commands.Cog):
    """レベルシステム"""

    def __init__(self, bot: SumireBot) -> None:
        self.bot = bot
        self.config = Config()
        self.db = Database()
        self.embed_builder = EmbedBuilder()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """メッセージ送信時のXP獲得処理"""
        # Botメッセージ、DM、システムメッセージは無視
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        user_id = message.author.id

        # レベルシステムが有効か確認
        settings = await self.db.get_leveling_settings(guild_id)
        if settings and not settings.get("enabled", True):
            return

        # 除外チャンネルか確認
        ignored_channels = settings.get("ignored_channels", []) if settings else []
        if message.channel.id in ignored_channels:
            return

        # クールダウン確認
        last_xp_time = await self.db.get_user_last_xp_time(guild_id, user_id)
        if last_xp_time:
            cooldown_end = last_xp_time + timedelta(seconds=XP_COOLDOWN_SECONDS)
            if datetime.utcnow() < cooldown_end:
                return

        # XP付与
        xp_amount = random.randint(XP_MIN, XP_MAX)
        new_xp, new_level, leveled_up = await self.db.add_user_xp(guild_id, user_id, xp_amount)

        if leveled_up:
            logger.info(f"レベルアップ: {message.author} -> Lv.{new_level} in {message.guild.name}")

    @app_commands.command(name="rank", description="レベルと経験値を表示します")
    @app_commands.describe(user="表示するユーザー（省略で自分）")
    async def rank(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.User] = None
    ) -> None:
        """ユーザーのレベルを表示"""
        await interaction.response.defer()

        target = user or interaction.user
        guild_id = interaction.guild.id

        # ユーザーデータを取得
        user_data = await self.db.get_user_level(guild_id, target.id)

        if not user_data:
            embed = self.embed_builder.info(
                title="レベル情報",
                description=f"{target.mention} はまだレベルデータがありません。\nメッセージを送信してXPを獲得しましょう！"
            )
            await interaction.followup.send(embed=embed)
            return

        level = user_data["level"]
        xp = user_data["xp"]
        next_level_xp = (level + 1) * 100

        # ランキング順位を取得
        rank = await self.db.get_user_rank(guild_id, target.id)

        # プログレスバーを作成
        progress = int((xp / next_level_xp) * 10) if next_level_xp > 0 else 10
        bar = "█" * progress + "░" * (10 - progress)
        percentage = int((xp / next_level_xp) * 100) if next_level_xp > 0 else 100

        embed = self.embed_builder.create(
            title=f"📊 {target.display_name} のレベル",
            color=target.accent_color or self.config.embed_color
        )

        embed.add_field(name="レベル", value=f"**{level}**", inline=True)
        embed.add_field(name="ランキング", value=f"**#{rank}**" if rank else "N/A", inline=True)
        embed.add_field(name="経験値", value=f"**{xp}** / {next_level_xp} XP", inline=True)
        embed.add_field(
            name="進捗",
            value=f"`{bar}` {percentage}%",
            inline=False
        )

        embed.set_author(name=str(target), icon_url=target.display_avatar.url)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text=f"ユーザーID: {target.id}")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="leaderboard", description="サーバーのレベルランキングを表示します")
    async def leaderboard(self, interaction: discord.Interaction) -> None:
        """サーバーのランキングを表示"""
        await interaction.response.defer()

        guild_id = interaction.guild.id
        leaderboard_data = await self.db.get_leaderboard(guild_id, limit=10)

        if not leaderboard_data:
            embed = self.embed_builder.info(
                title="レベルランキング",
                description="まだランキングデータがありません。\nメッセージを送信してXPを獲得しましょう！"
            )
            await interaction.followup.send(embed=embed)
            return

        embed = self.embed_builder.create(
            title="🏆 レベルランキング",
            description=f"**{interaction.guild.name}** のトップ10",
            color=0xFFD700
        )

        leaderboard_text = ""
        medals = ["🥇", "🥈", "🥉"]

        for idx, data in enumerate(leaderboard_data, 1):
            medal = medals[idx - 1] if idx <= 3 else f"**{idx}.**"
            user_id = data["user_id"]
            level = data["level"]
            xp = data["xp"]

            leaderboard_text += f"{medal} <@{user_id}> - Lv.**{level}** ({xp} XP)\n"

        embed.add_field(
            name="ランキング",
            value=leaderboard_text[:1024],
            inline=False
        )

        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text=f"リクエスト: {interaction.user}")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="leveling", description="レベルシステムを設定します")
    @app_commands.default_permissions(administrator=True)
    @Checks.is_admin()
    async def leveling_settings(self, interaction: discord.Interaction) -> None:
        """レベルシステム設定コマンド"""
        if not interaction.guild:
            embed = self.embed_builder.error(
                title="エラー",
                description="このコマンドはサーバー内でのみ使用できます。"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # 現在の設定を取得
        settings = await self.db.get_leveling_settings(interaction.guild.id)
        enabled = bool(settings.get("enabled", 1)) if settings else True
        ignored_channels = settings.get("ignored_channels", []) if settings else []

        # 設定パネルを表示
        view = LevelingSettingsView(
            guild=interaction.guild,
            enabled=enabled,
            ignored_channels=ignored_channels
        )

        await interaction.response.send_message(view=view, ephemeral=True)

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ) -> None:
        """コマンドエラーハンドリング"""
        await handle_app_command_error(interaction, error, "Leveling")


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(Leveling(bot))
