"""
Owner コマンド（shutdown, restart, sync）
"""
from __future__ import annotations

import sys

import discord
from discord import app_commands

from utils.logging import get_logger
from views.common_views import (
    CommonErrorView,
    CommonSuccessView,
    CommonWarningView,
    CommonInfoView
)

logger = get_logger("sumire.cogs.admin.owner")

# 再起動用の終了コード
RESTART_EXIT_CODE = 26


class OwnerMixin:
    """オーナー専用コマンド Mixin"""

    def _is_owner(self, user_id: int) -> bool:
        """オーナーかどうかチェック"""
        return user_id == self.config.owner_id

    @app_commands.command(name="shutdown", description="Botをシャットダウンします（オーナー専用）")
    async def shutdown(self, interaction: discord.Interaction) -> None:
        """Botをシャットダウン"""
        if not self._is_owner(interaction.user.id):
            view = CommonErrorView(
                title="権限エラー",
                description="このコマンドはBotオーナーのみ使用できます。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        view = CommonInfoView(
            title="シャットダウン",
            description="Botをシャットダウンしています..."
        )
        await interaction.response.send_message(view=view)

        logger.info(f"シャットダウン実行: {interaction.user}")
        await self.bot.close()

    @app_commands.command(name="restart", description="Botを再起動します（オーナー専用）")
    async def restart(self, interaction: discord.Interaction) -> None:
        """Botを再起動"""
        if not self._is_owner(interaction.user.id):
            view = CommonErrorView(
                title="権限エラー",
                description="このコマンドはBotオーナーのみ使用できます。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        view = CommonInfoView(
            title="再起動",
            description="Botを再起動しています...\n-# 起動スクリプトを使用している場合のみ自動再起動されます"
        )
        await interaction.response.send_message(view=view)

        logger.info(f"再起動実行: {interaction.user}")
        await self.bot.close()
        sys.exit(RESTART_EXIT_CODE)

    @app_commands.command(name="sync", description="Cogをリロードしてコマンドを同期します（オーナー専用）")
    @app_commands.describe(
        cog="リロードするCog名（空欄で全Cog）",
        reload="Cogをリロードするか（デフォルト: True）"
    )
    async def sync(
        self,
        interaction: discord.Interaction,
        cog: str = None,
        reload: bool = True
    ) -> None:
        """Cogリロード + コマンド同期"""
        if not self._is_owner(interaction.user.id):
            view = CommonErrorView(
                title="権限エラー",
                description="このコマンドはBotオーナーのみ使用できます。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        result_lines = []

        # リロード対象のCogリスト
        cog_list = [
            "cogs.general",
            "cogs.utility",
            "cogs.ticket",
            "cogs.moderation",
            "cogs.music",
            "cogs.leveling",
            "cogs.admin",
        ]

        # Cogリロード
        if reload:
            if cog:
                cog_name = cog if cog.startswith("cogs.") else f"cogs.{cog}"
                if cog_name not in cog_list:
                    view = CommonErrorView(
                        title="エラー",
                        description=f"Cog `{cog}` は存在しません。"
                    )
                    await interaction.followup.send(view=view, ephemeral=True)
                    return

                try:
                    await self.bot.reload_extension(cog_name)
                    result_lines.append(f"✅ `{cog_name}` をリロード")
                    logger.info(f"Cogリロード: {cog_name} by {interaction.user}")
                except Exception as e:
                    result_lines.append(f"❌ `{cog_name}` リロード失敗: {e}")
                    logger.error(f"Cogリロードエラー: {cog_name} - {e}")
            else:
                success_count = 0
                fail_count = 0

                for cog_name in cog_list:
                    try:
                        await self.bot.reload_extension(cog_name)
                        success_count += 1
                    except Exception as e:
                        fail_count += 1
                        logger.error(f"Cogリロードエラー: {cog_name} - {e}")

                if fail_count > 0:
                    result_lines.append(f"⚠️ Cogリロード: {success_count}成功 / {fail_count}失敗")
                else:
                    result_lines.append(f"✅ 全{success_count}個のCogをリロード")
                logger.info(f"全Cogリロード: 成功={success_count}, 失敗={fail_count} by {interaction.user}")

        # コマンド同期
        try:
            synced = await self.bot.tree.sync()
            result_lines.append(f"✅ {len(synced)}個のコマンドを同期")
            logger.info(f"コマンド同期: {len(synced)} 個 by {interaction.user}")
        except Exception as e:
            result_lines.append(f"❌ コマンド同期失敗: {e}")
            logger.error(f"コマンド同期エラー: {e}")

        # 結果表示
        has_error = any("❌" in line for line in result_lines)
        has_warning = any("⚠️" in line for line in result_lines)

        if has_error:
            view = CommonErrorView(
                title="同期完了（エラーあり）",
                description="\n".join(result_lines)
            )
        elif has_warning:
            view = CommonWarningView(
                title="同期完了（警告あり）",
                description="\n".join(result_lines)
            )
        else:
            view = CommonSuccessView(
                title="同期完了",
                description="\n".join(result_lines)
            )

        await interaction.followup.send(view=view, ephemeral=True)

    @sync.autocomplete("cog")
    async def sync_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        """syncコマンドのCogオートコンプリート"""
        cogs = [
            "general", "utility", "ticket", "moderation",
            "music", "leveling", "admin"
        ]
        return [
            app_commands.Choice(name=cog, value=cog)
            for cog in cogs if current.lower() in cog.lower()
        ][:25]
