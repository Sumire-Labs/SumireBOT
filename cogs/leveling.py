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


class RankView(ui.LayoutView):
    """
    ランク表示用View
    Components V2 (LayoutView + Container) を使用
    """

    def __init__(
        self,
        target: discord.User,
        level: int,
        xp: int,
        text_rank: int,
        vc_level: int,
        vc_time: int,
        vc_rank: int
    ) -> None:
        super().__init__(timeout=300)

        next_level_xp = (level + 1) * 100

        # プログレスバー計算
        text_progress = int((xp / next_level_xp) * 10) if next_level_xp > 0 else 10
        text_bar = "█" * text_progress + "░" * (10 - text_progress)
        text_percentage = int((xp / next_level_xp) * 100) if next_level_xp > 0 else 100

        vc_progress_seconds = vc_time % 3600
        vc_progress = int((vc_progress_seconds / 3600) * 10)
        vc_bar = "█" * vc_progress + "░" * (10 - vc_progress)
        vc_percentage = int((vc_progress_seconds / 3600) * 100)

        # VC時間フォーマット
        hours = vc_time // 3600
        minutes = (vc_time % 3600) // 60
        if hours > 0:
            vc_time_str = f"{hours}時間{minutes}分"
        elif minutes > 0:
            vc_time_str = f"{minutes}分"
        else:
            vc_time_str = "0分"

        # Container を作成
        container = ui.Container(accent_colour=discord.Colour.blurple())

        # ヘッダーセクション
        header_section = ui.Section(
            ui.TextDisplay(f"# {target.display_name} のステータス"),
            accessory=ui.Thumbnail(target.display_avatar.url)
        )
        container.add_item(header_section)
        container.add_item(ui.Separator())

        # テキストレベルセクション
        container.add_item(ui.TextDisplay(
            f"### 💬 テキストレベル\n"
            f"**Lv.{level}** (#{text_rank if text_rank else 'N/A'})\n"
            f"{xp} / {next_level_xp} XP\n"
            f"`{text_bar}` {text_percentage}%"
        ))

        container.add_item(ui.Separator())

        # VCレベルセクション
        container.add_item(ui.TextDisplay(
            f"### 🎤 VCレベル\n"
            f"**Lv.{vc_level}** (#{vc_rank if vc_rank else 'N/A'})\n"
            f"合計: {vc_time_str}\n"
            f"`{vc_bar}` {vc_percentage}%"
        ))

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# ユーザーID: {target.id}"))

        self.add_item(container)


class LeaderboardView(ui.LayoutView):
    """
    ランキング表示用View
    Components V2 (LayoutView + Container) を使用
    """

    def __init__(
        self,
        guild: discord.Guild,
        text_leaderboard: list[dict],
        vc_leaderboard: list[dict]
    ) -> None:
        super().__init__(timeout=300)

        medals = ["🥇", "🥈", "🥉"]

        # Container を作成
        container = ui.Container(accent_colour=discord.Colour.gold())

        # ヘッダー
        if guild.icon:
            header_section = ui.Section(
                ui.TextDisplay(f"# 🏆 サーバーランキング\n**{guild.name}** のトップ10"),
                accessory=ui.Thumbnail(guild.icon.url)
            )
            container.add_item(header_section)
        else:
            container.add_item(ui.TextDisplay(f"# 🏆 サーバーランキング\n**{guild.name}** のトップ10"))

        container.add_item(ui.Separator())

        # テキストランキング
        if text_leaderboard:
            text_ranking = ""
            for idx, data in enumerate(text_leaderboard, 1):
                medal = medals[idx - 1] if idx <= 3 else f"**{idx}.**"
                text_ranking += f"{medal} <@{data['user_id']}> Lv.**{data['level']}**\n"
            container.add_item(ui.TextDisplay(f"### 💬 テキストランキング\n{text_ranking}"))
        else:
            container.add_item(ui.TextDisplay("### 💬 テキストランキング\nデータなし"))

        container.add_item(ui.Separator())

        # VCランキング
        if vc_leaderboard:
            vc_ranking = ""
            for idx, data in enumerate(vc_leaderboard, 1):
                medal = medals[idx - 1] if idx <= 3 else f"**{idx}.**"
                vc_ranking += f"{medal} <@{data['user_id']}> Lv.**{data['vc_level']}**\n"
            container.add_item(ui.TextDisplay(f"### 🎤 VCランキング\n{vc_ranking}"))
        else:
            container.add_item(ui.TextDisplay("### 🎤 VCランキング\nデータなし"))

        self.add_item(container)


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

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ) -> None:
        """VC参加/退出時の時間トラッキング"""
        if member.bot:
            return

        guild_id = member.guild.id
        user_id = member.id

        # レベルシステムが有効か確認
        settings = await self.db.get_leveling_settings(guild_id)
        if settings and not settings.get("enabled", True):
            return

        # VCに参加した場合
        if before.channel is None and after.channel is not None:
            await self.db.set_vc_join_time(guild_id, user_id)
            logger.debug(f"VC参加: {member} in {after.channel.name}")

        # VCから退出した場合
        elif before.channel is not None and after.channel is None:
            vc_time, vc_level, leveled_up = await self.db.add_vc_time(guild_id, user_id)
            if leveled_up:
                logger.info(f"VCレベルアップ: {member} -> VCLv.{vc_level} in {member.guild.name}")

        # 別のVCに移動した場合（時間は継続）
        elif before.channel is not None and after.channel is not None and before.channel != after.channel:
            logger.debug(f"VC移動: {member} {before.channel.name} -> {after.channel.name}")

    def _format_time(self, seconds: int) -> str:
        """秒数を時間:分:秒形式にフォーマット"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}時間{minutes}分"
        elif minutes > 0:
            return f"{minutes}分{secs}秒"
        else:
            return f"{secs}秒"

    @app_commands.command(name="rank", description="レベルと経験値を表示します")
    @app_commands.describe(user="表示するユーザー（省略で自分）")
    async def rank(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.User] = None
    ) -> None:
        """ユーザーのレベルを表示"""
        target = user or interaction.user
        guild_id = interaction.guild.id

        # ユーザーデータを取得
        user_data = await self.db.get_user_level(guild_id, target.id)

        if not user_data:
            embed = self.embed_builder.info(
                title="レベル情報",
                description=f"{target.mention} はまだレベルデータがありません。\nメッセージを送信またはVCに参加しましょう！"
            )
            await interaction.response.send_message(embed=embed)
            return

        # ランキング順位を取得
        text_rank = await self.db.get_user_rank(guild_id, target.id)
        vc_rank = await self.db.get_user_vc_rank(guild_id, target.id)

        # Components V2 Viewを作成
        view = RankView(
            target=target,
            level=user_data["level"],
            xp=user_data["xp"],
            text_rank=text_rank,
            vc_level=user_data.get("vc_level", 0),
            vc_time=user_data.get("vc_time", 0),
            vc_rank=vc_rank
        )

        await interaction.response.send_message(view=view)

    @app_commands.command(name="leaderboard", description="サーバーのレベルランキングを表示します")
    async def leaderboard(self, interaction: discord.Interaction) -> None:
        """サーバーのランキングを表示"""
        guild_id = interaction.guild.id
        text_leaderboard = await self.db.get_leaderboard(guild_id, limit=10)
        vc_leaderboard = await self.db.get_vc_leaderboard(guild_id, limit=10)

        if not text_leaderboard and not vc_leaderboard:
            embed = self.embed_builder.info(
                title="ランキング",
                description="まだランキングデータがありません。\nメッセージを送信またはVCに参加しましょう！"
            )
            await interaction.response.send_message(embed=embed)
            return

        # Components V2 Viewを作成
        view = LeaderboardView(
            guild=interaction.guild,
            text_leaderboard=text_leaderboard,
            vc_leaderboard=vc_leaderboard
        )

        await interaction.response.send_message(view=view)

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
