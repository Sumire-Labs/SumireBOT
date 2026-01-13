"""
チケットシステム Cog
サポートチケットの作成・管理
"""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from utils.config import Config
from utils.database import Database
from utils.embeds import EmbedBuilder
from utils.checks import Checks, handle_app_command_error
from utils.logging import get_logger
from views.ticket_views import TicketPanelView
from views.persistent import PersistentViewManager

logger = get_logger("sumire.cogs.ticket")


class Ticket(commands.Cog):
    """チケットシステム"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.config = Config()
        self.db = Database()
        self.embed_builder = EmbedBuilder()

    @app_commands.command(name="ticket", description="チケットパネルを設置します")
    @app_commands.default_permissions(administrator=True)
    @Checks.is_admin()
    async def ticket_setup(self, interaction: discord.Interaction) -> None:
        """
        チケットシステムをセットアップするコマンド
        実行チャンネルにチケットパネルを設置
        """
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        channel = interaction.channel

        # 既存の設定をチェック
        existing = await self.db.get_ticket_settings(guild.id)
        if existing and existing.get("panel_message_id"):
            # 既存パネルがある場合は確認
            try:
                old_channel = guild.get_channel(existing["panel_channel_id"])
                if old_channel:
                    old_message = await old_channel.fetch_message(existing["panel_message_id"])
                    if old_message:
                        embed = self.embed_builder.warning(
                            title="既存のパネルがあります",
                            description=f"既にチケットパネルが設置されています。\n"
                                       f"{old_channel.mention}\n\n"
                                       f"新しいパネルを設置するには、先に既存のパネルを削除してください。"
                        )
                        await interaction.followup.send(embed=embed)
                        return
            except discord.NotFound:
                pass  # 古いパネルが見つからない場合は続行

        # チケット用カテゴリを作成または取得
        category_name = "📫 チケット"
        category = discord.utils.get(guild.categories, name=category_name)

        if not category:
            try:
                # カテゴリを作成
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
                embed = self.embed_builder.error(
                    title="権限エラー",
                    description="カテゴリを作成する権限がありません。"
                )
                await interaction.followup.send(embed=embed)
                return

        # チケットパネルを送信（Components V2 - LayoutView）
        panel_view = TicketPanelView(self.bot)

        try:
            panel_message = await channel.send(view=panel_view)
        except discord.Forbidden:
            embed = self.embed_builder.error(
                title="権限エラー",
                description="メッセージを送信する権限がありません。"
            )
            await interaction.followup.send(embed=embed)
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
        embed = self.embed_builder.success(
            title="チケットシステムを設定しました",
            description="チケットパネルを設置しました。"
        )
        embed.add_field(
            name="パネル",
            value=f"[パネルへジャンプ]({panel_message.jump_url})",
            inline=True
        )
        embed.add_field(
            name="カテゴリ",
            value=category.mention,
            inline=True
        )
        embed.add_field(
            name="📋 使い方",
            value="ユーザーがパネルのボタンをクリックすると、\n"
                  "自動的にチケットチャンネルが作成されます。",
            inline=False
        )

        await interaction.followup.send(embed=embed)
        logger.info(f"チケットシステムセットアップ完了: guild={guild.name}")

    # ==================== エラーハンドリング ====================

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ) -> None:
        """コマンドエラーハンドリング"""
        await handle_app_command_error(interaction, error, "Ticket")


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(Ticket(bot))
