"""
Timeout コマンド
"""
from __future__ import annotations

from datetime import timedelta
from typing import Optional

import discord
from discord import app_commands

from utils.checks import Checks
from utils.logging import get_logger
from views.moderation_views import ModerationSuccessView
from views.common_views import CommonErrorView

logger = get_logger("sumire.cogs.moderation")

# Timeout期間のプリセット（分単位）
TIMEOUT_DURATIONS = [
    app_commands.Choice(name="1分", value=1),
    app_commands.Choice(name="5分", value=5),
    app_commands.Choice(name="10分", value=10),
    app_commands.Choice(name="1時間", value=60),
    app_commands.Choice(name="1日", value=1440),
    app_commands.Choice(name="1週間", value=10080),
]


class TimeoutMixin:
    """Timeoutコマンド Mixin"""

    @app_commands.command(name="timeout", description="メンバーをタイムアウトします")
    @app_commands.describe(
        member="タイムアウトするメンバー",
        duration="タイムアウトの期間",
        reason="タイムアウトの理由"
    )
    @app_commands.choices(duration=TIMEOUT_DURATIONS)
    @app_commands.default_permissions(moderate_members=True)
    @Checks.has_permissions(moderate_members=True)
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        duration: int,
        reason: Optional[str] = None
    ) -> None:
        """メンバーをタイムアウトするコマンド"""
        if not interaction.guild:
            view = CommonErrorView(
                title="エラー",
                description="このコマンドはサーバー内でのみ使用できます。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        reason = reason or "理由なし"
        duration_text = self._format_duration(duration)

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
            action_type="timeout",
            guild_name=interaction.guild.name,
            reason=reason,
            duration=duration_text
        )

        # タイムアウト実行
        try:
            await member.timeout(
                timedelta(minutes=duration),
                reason=f"{reason} (by {interaction.user})"
            )
            logger.info(f"TIMEOUT: {member} timed out for {duration_text} by {interaction.user} in {interaction.guild.name}")
        except discord.Forbidden:
            view = CommonErrorView(
                title="エラー",
                description="権限不足でタイムアウトできません。Botのロール位置を確認してください。"
            )
            await interaction.followup.send(view=view, ephemeral=True)
            return
        except discord.HTTPException as e:
            view = CommonErrorView(
                title="エラー",
                description=f"タイムアウト処理中にエラーが発生しました: {e}"
            )
            await interaction.followup.send(view=view, ephemeral=True)
            return

        # ログ送信
        await self._send_log(
            guild_id=interaction.guild.id,
            action_type="timeout",
            target=member,
            moderator=interaction.user,
            reason=reason,
            duration=duration_text
        )

        # 成功レスポンス
        view = ModerationSuccessView(
            action_type="timeout",
            target_name=str(member),
            target_avatar=member.display_avatar.url,
            reason=reason,
            duration=duration_text,
            dm_sent=dm_sent
        )
        await interaction.followup.send(view=view)
