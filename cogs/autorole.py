"""
自動ロール付与 Cog
サーバー参加時に自動でロールを付与する機能
"""
from __future__ import annotations

import discord
from discord import app_commands, ui
from discord.ext import commands
from typing import TYPE_CHECKING, Optional

from utils.config import Config
from utils.database import Database
from utils.embeds import EmbedBuilder
from utils.logging import get_logger

if TYPE_CHECKING:
    from bot import SumireBot

logger = get_logger("sumire.cogs.autorole")


class AutoRoleSettingsView(ui.LayoutView):
    """
    自動ロール設定パネル
    Components V2 (LayoutView + Container) を使用
    """

    def __init__(
        self,
        guild: discord.Guild,
        human_role: Optional[discord.Role] = None,
        bot_role: Optional[discord.Role] = None,
        enabled: bool = True
    ) -> None:
        super().__init__(timeout=300)
        self.guild = guild
        self.db = Database()
        self.config = Config()

        # Container を作成
        container = ui.Container(accent_colour=discord.Colour.purple())

        # ヘッダー
        container.add_item(ui.TextDisplay("# 🎭 自動ロール設定"))
        container.add_item(ui.TextDisplay(
            "サーバーに参加したメンバーに自動でロールを付与します。\n"
            "人間とBotで別々のロールを設定できます。"
        ))
        container.add_item(ui.Separator())

        # 現在の設定表示
        status_emoji = "🟢 有効" if enabled else "🔴 無効"
        human_text = human_role.mention if human_role else "未設定"
        bot_text = bot_role.mention if bot_role else "未設定"

        container.add_item(ui.TextDisplay(
            f"**現在の設定**\n"
            f"ステータス: {status_emoji}\n"
            f"人間用ロール: {human_text}\n"
            f"Bot用ロール: {bot_text}"
        ))
        container.add_item(ui.Separator())

        # 人間用ロール選択
        container.add_item(ui.TextDisplay("**👤 人間用ロール**"))
        human_row = ui.ActionRow()
        human_select = ui.RoleSelect(
            placeholder="人間用ロールを選択...",
            custom_id="autorole:select:human",
            min_values=0,
            max_values=1
        )
        human_row.add_item(human_select)
        container.add_item(human_row)

        # Bot用ロール選択
        container.add_item(ui.TextDisplay("**🤖 Bot用ロール**"))
        bot_row = ui.ActionRow()
        bot_select = ui.RoleSelect(
            placeholder="Bot用ロールを選択...",
            custom_id="autorole:select:bot",
            min_values=0,
            max_values=1
        )
        bot_row.add_item(bot_select)
        container.add_item(bot_row)

        container.add_item(ui.Separator())

        # 操作ボタン
        button_row = ui.ActionRow()
        toggle_label = "🔴 無効化" if enabled else "🟢 有効化"
        toggle_style = discord.ButtonStyle.danger if enabled else discord.ButtonStyle.success
        button_row.add_item(ui.Button(
            label=toggle_label,
            style=toggle_style,
            custom_id="autorole:toggle"
        ))
        button_row.add_item(ui.Button(
            label="🗑️ 人間用をクリア",
            style=discord.ButtonStyle.secondary,
            custom_id="autorole:clear:human"
        ))
        button_row.add_item(ui.Button(
            label="🗑️ Bot用をクリア",
            style=discord.ButtonStyle.secondary,
            custom_id="autorole:clear:bot"
        ))
        container.add_item(button_row)

        # ContainerをLayoutViewに追加
        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """インタラクションのチェックとルーティング"""
        custom_id = interaction.data.get("custom_id", "")

        if custom_id == "autorole:select:human":
            await self.set_human_role(interaction)
            return False
        elif custom_id == "autorole:select:bot":
            await self.set_bot_role(interaction)
            return False
        elif custom_id == "autorole:toggle":
            await self.toggle_enabled(interaction)
            return False
        elif custom_id == "autorole:clear:human":
            await self.clear_role(interaction, "human")
            return False
        elif custom_id == "autorole:clear:bot":
            await self.clear_role(interaction, "bot")
            return False

        return True

    async def set_human_role(self, interaction: discord.Interaction) -> None:
        """人間用ロールを設定"""
        await interaction.response.defer(ephemeral=True)

        values = interaction.data.get("values", [])
        if not values:
            embed = EmbedBuilder().warning(
                title="ロール未選択",
                description="ロールが選択されていません。"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        role_id = int(values[0])
        role = interaction.guild.get_role(role_id)

        if not role:
            embed = EmbedBuilder().error(
                title="エラー",
                description="ロールが見つかりません。"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # 権限チェック
        if role >= interaction.guild.me.top_role:
            embed = EmbedBuilder().error(
                title="権限エラー",
                description="Botより上位のロールは設定できません。"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        await self.db.set_autorole(interaction.guild.id, human_role_id=role_id)

        embed = EmbedBuilder().success(
            title="人間用ロールを設定しました",
            description=f"ロール: {role.mention}\n\n"
                       f"新しく参加した人間メンバーにこのロールが自動付与されます。"
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

        logger.info(f"AutoRole 人間用ロール設定: {role.name} in {interaction.guild.name}")

    async def set_bot_role(self, interaction: discord.Interaction) -> None:
        """Bot用ロールを設定"""
        await interaction.response.defer(ephemeral=True)

        values = interaction.data.get("values", [])
        if not values:
            embed = EmbedBuilder().warning(
                title="ロール未選択",
                description="ロールが選択されていません。"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        role_id = int(values[0])
        role = interaction.guild.get_role(role_id)

        if not role:
            embed = EmbedBuilder().error(
                title="エラー",
                description="ロールが見つかりません。"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # 権限チェック
        if role >= interaction.guild.me.top_role:
            embed = EmbedBuilder().error(
                title="権限エラー",
                description="Botより上位のロールは設定できません。"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        await self.db.set_autorole(interaction.guild.id, bot_role_id=role_id)

        embed = EmbedBuilder().success(
            title="Bot用ロールを設定しました",
            description=f"ロール: {role.mention}\n\n"
                       f"新しく参加したBotにこのロールが自動付与されます。"
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

        logger.info(f"AutoRole Bot用ロール設定: {role.name} in {interaction.guild.name}")

    async def toggle_enabled(self, interaction: discord.Interaction) -> None:
        """有効/無効を切り替え"""
        await interaction.response.defer(ephemeral=True)

        settings = await self.db.get_autorole_settings(interaction.guild.id)
        current_enabled = settings.get("enabled", 1) if settings else 1
        new_enabled = not bool(current_enabled)

        await self.db.set_autorole(interaction.guild.id, enabled=new_enabled)

        status_text = "有効" if new_enabled else "無効"
        embed = EmbedBuilder().success(
            title=f"自動ロールを{status_text}にしました",
            description=f"ステータス: {'🟢 有効' if new_enabled else '🔴 無効'}"
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

        logger.info(f"AutoRole {status_text}: {interaction.guild.name}")

    async def clear_role(self, interaction: discord.Interaction, role_type: str) -> None:
        """ロール設定をクリア"""
        await interaction.response.defer(ephemeral=True)

        await self.db.clear_autorole(interaction.guild.id, role_type)

        type_text = "人間用" if role_type == "human" else "Bot用"
        embed = EmbedBuilder().success(
            title=f"{type_text}ロールをクリアしました",
            description=f"{type_text}ロールの設定を解除しました。"
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

        logger.info(f"AutoRole {type_text}ロールクリア: {interaction.guild.name}")


class AutoRole(commands.Cog):
    """自動ロール付与"""

    def __init__(self, bot: SumireBot) -> None:
        self.bot = bot
        self.config = Config()
        self.db = Database()
        self.embed_builder = EmbedBuilder()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """メンバー参加時のロール付与"""
        guild = member.guild

        # 設定を取得
        settings = await self.db.get_autorole_settings(guild.id)
        if not settings or not settings.get("enabled", 1):
            return

        # 付与するロールを決定
        if member.bot:
            role_id = settings.get("bot_role_id")
            role_type = "Bot"
        else:
            role_id = settings.get("human_role_id")
            role_type = "人間"

        if not role_id:
            return

        role = guild.get_role(role_id)
        if not role:
            logger.warning(f"AutoRole: ロールが見つかりません role_id={role_id}")
            return

        # 権限チェック
        if role >= guild.me.top_role:
            logger.warning(f"AutoRole: 権限不足でロールを付与できません role={role.name}")
            return

        try:
            await member.add_roles(role, reason=f"AutoRole: {role_type}メンバー参加")
            logger.info(f"AutoRole: {role.name} を {member} に付与 ({role_type})")
        except discord.Forbidden:
            logger.error(f"AutoRole: ロール付与権限なし role={role.name}, member={member}")
        except discord.HTTPException as e:
            logger.error(f"AutoRole: ロール付与エラー: {e}")

    @app_commands.command(name="autorole", description="自動ロール付与の設定を行います")
    @app_commands.default_permissions(manage_roles=True)
    async def autorole(self, interaction: discord.Interaction) -> None:
        """自動ロール設定コマンド"""
        if not interaction.guild:
            embed = self.embed_builder.error(
                title="エラー",
                description="このコマンドはサーバー内でのみ使用できます。"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # 現在の設定を取得
        settings = await self.db.get_autorole_settings(interaction.guild.id)

        human_role = None
        bot_role = None
        enabled = True

        if settings:
            if settings.get("human_role_id"):
                human_role = interaction.guild.get_role(settings["human_role_id"])
            if settings.get("bot_role_id"):
                bot_role = interaction.guild.get_role(settings["bot_role_id"])
            enabled = bool(settings.get("enabled", 1))

        # 設定パネルを表示
        view = AutoRoleSettingsView(
            guild=interaction.guild,
            human_role=human_role,
            bot_role=bot_role,
            enabled=enabled
        )

        await interaction.response.send_message(view=view, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(AutoRole(bot))
