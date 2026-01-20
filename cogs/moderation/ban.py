"""
Ban コマンド
"""
from __future__ import annotations

from typing import Optional

import discord
from discord import app_commands

from utils.checks import Checks
from utils.logging import get_logger
from views.moderation_views import ModerationSuccessView
from views.common_views import CommonErrorView

logger = get_logger("sumire.cogs.moderation")


class BanMixin:
    """Banコマンド Mixin"""

    @app_commands.command(name="ban", description="ユーザーをサーバーからBANします")
    @app_commands.describe(
        user="BANするユーザー",
        reason="BANの理由"
    )
    @app_commands.default_permissions(ban_members=True)
    @Checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        reason: Optional[str] = None
    ) -> None:
        """ユーザーをBANするコマンド"""
        if not interaction.guild:
            view = CommonErrorView(
                title="エラー",
                description="このコマンドはサーバー内でのみ使用できます。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        reason = reason or "理由なし"

        # メンバーとして取得可能な場合はロール階層チェック
        member = interaction.guild.get_member(user.id)
        if member:
            can_moderate, error_msg = self._can_moderate(interaction.user, member, interaction.guild)
            if not can_moderate:
                view = CommonErrorView(title="エラー", description=error_msg)
                await interaction.response.send_message(view=view, ephemeral=True)
                return

        await interaction.response.defer()

        # DM通知
        dm_sent = await self._send_dm_notification(
            user=user,
            action_type="ban",
            guild_name=interaction.guild.name,
            reason=reason
        )

        # BAN実行
        try:
            await interaction.guild.ban(user, reason=f"{reason} (by {interaction.user})")
            logger.info(f"BAN: {user} banned by {interaction.user} in {interaction.guild.name}")
        except discord.Forbidden:
            view = CommonErrorView(
                title="エラー",
                description="権限不足でBANできません。Botのロール位置を確認してください。"
            )
            await interaction.followup.send(view=view, ephemeral=True)
            return
        except discord.HTTPException as e:
            view = CommonErrorView(
                title="エラー",
                description=f"BAN処理中にエラーが発生しました: {e}"
            )
            await interaction.followup.send(view=view, ephemeral=True)
            return

        # ログ送信
        await self._send_log(
            guild_id=interaction.guild.id,
            action_type="ban",
            target=user,
            moderator=interaction.user,
            reason=reason
        )

        # 成功レスポンス
        view = ModerationSuccessView(
            action_type="ban",
            target_name=str(user),
            target_avatar=user.display_avatar.url,
            reason=reason,
            dm_sent=dm_sent
        )
        await interaction.followup.send(view=view)
