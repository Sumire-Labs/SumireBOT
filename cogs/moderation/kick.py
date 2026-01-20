"""
Kick コマンド
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


class KickMixin:
    """Kickコマンド Mixin"""

    @app_commands.command(name="kick", description="メンバーをサーバーからキックします")
    @app_commands.describe(
        member="キックするメンバー",
        reason="キックの理由"
    )
    @app_commands.default_permissions(kick_members=True)
    @Checks.has_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: Optional[str] = None
    ) -> None:
        """メンバーをキックするコマンド"""
        if not interaction.guild:
            view = CommonErrorView(
                title="エラー",
                description="このコマンドはサーバー内でのみ使用できます。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        reason = reason or "理由なし"

        # ロール階層チェック
        can_moderate, error_msg = self._can_moderate(interaction.user, member, interaction.guild)
        if not can_moderate:
            view = CommonErrorView(title="エラー", description=error_msg)
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        await interaction.response.defer()

        # DM通知
        dm_sent = await self._send_dm_notification(
            user=member,
            action_type="kick",
            guild_name=interaction.guild.name,
            reason=reason
        )

        # キック実行
        try:
            await member.kick(reason=f"{reason} (by {interaction.user})")
            logger.info(f"KICK: {member} kicked by {interaction.user} in {interaction.guild.name}")
        except discord.Forbidden:
            view = CommonErrorView(
                title="エラー",
                description="権限不足でキックできません。Botのロール位置を確認してください。"
            )
            await interaction.followup.send(view=view, ephemeral=True)
            return
        except discord.HTTPException as e:
            view = CommonErrorView(
                title="エラー",
                description=f"キック処理中にエラーが発生しました: {e}"
            )
            await interaction.followup.send(view=view, ephemeral=True)
            return

        # ログ送信
        await self._send_log(
            guild_id=interaction.guild.id,
            action_type="kick",
            target=member,
            moderator=interaction.user,
            reason=reason
        )

        # 成功レスポンス
        view = ModerationSuccessView(
            action_type="kick",
            target_name=str(member),
            target_avatar=member.display_avatar.url,
            reason=reason,
            dm_sent=dm_sent
        )
        await interaction.followup.send(view=view)
