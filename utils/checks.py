"""
パーミッションチェックユーティリティ
"""
from __future__ import annotations

import discord
from discord import app_commands, ui
from typing import Callable, TypeVar, Optional
from functools import wraps

from views.common_views import CommonErrorView, CommonWarningView
from utils.logging import get_logger

T = TypeVar("T")
logger = get_logger("sumire.utils.checks")


class Checks:
    """コマンドパーミッションチェック"""

    @staticmethod
    def is_admin() -> Callable[[T], T]:
        """管理者権限チェックデコレーター"""
        async def predicate(interaction: discord.Interaction) -> bool:
            if not interaction.guild:
                return False
            return interaction.user.guild_permissions.administrator

        return app_commands.check(predicate)

    @staticmethod
    def has_permissions(**perms: bool) -> Callable[[T], T]:
        """指定された権限を持っているかチェック"""
        async def predicate(interaction: discord.Interaction) -> bool:
            if not interaction.guild:
                return False
            permissions = interaction.user.guild_permissions
            return all(
                getattr(permissions, perm, False) == value
                for perm, value in perms.items()
            )

        return app_commands.check(predicate)

    @staticmethod
    def is_owner() -> Callable[[T], T]:
        """サーバーオーナーかチェック"""
        async def predicate(interaction: discord.Interaction) -> bool:
            if not interaction.guild:
                return False
            return interaction.user.id == interaction.guild.owner_id

        return app_commands.check(predicate)

    @staticmethod
    def in_guild() -> Callable[[T], T]:
        """サーバー内でのみ実行可能"""
        async def predicate(interaction: discord.Interaction) -> bool:
            return interaction.guild is not None

        return app_commands.check(predicate)


class CheckFailure(app_commands.CheckFailure):
    """カスタムチェック失敗例外"""
    pass


class NotAdministrator(CheckFailure):
    """管理者権限がない場合"""
    def __init__(self):
        super().__init__("このコマンドは管理者権限が必要です。")


class NotInGuild(CheckFailure):
    """サーバー内で実行されていない場合"""
    def __init__(self):
        super().__init__("このコマンドはサーバー内でのみ使用できます。")


class MissingPermissions(CheckFailure):
    """特定の権限が不足している場合"""
    def __init__(self, permissions: list[str]):
        self.permissions = permissions
        perms_str = ", ".join(permissions)
        super().__init__(f"必要な権限がありません: {perms_str}")


async def handle_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
    cog_name: Optional[str] = None
) -> bool:
    """
    共通のコマンドエラーハンドリング

    Args:
        interaction: Discord Interaction
        error: 発生したエラー
        cog_name: ログ用のCog名（オプション）

    Returns:
        bool: エラーが処理された場合True
    """
    if isinstance(error, app_commands.CheckFailure):
        # 権限チェック失敗
        if isinstance(error, NotAdministrator):
            description = "このコマンドを実行する権限がありません。\n管理者権限が必要です。"
        elif isinstance(error, NotInGuild):
            description = "このコマンドはサーバー内でのみ使用できます。"
        elif isinstance(error, MissingPermissions):
            perms_str = "、".join(error.permissions)
            description = f"このコマンドを実行する権限がありません。\n必要な権限: {perms_str}"
        else:
            description = "このコマンドを実行する権限がありません。\n管理者権限が必要です。"

        view = CommonErrorView(
            title="権限エラー",
            description=description
        )
        await _send_error_response(interaction, view)
        return True

    elif isinstance(error, app_commands.CommandOnCooldown):
        # クールダウン中
        view = CommonWarningView(
            title="クールダウン中",
            description=f"このコマンドは {error.retry_after:.1f} 秒後に再度使用できます。"
        )
        await _send_error_response(interaction, view)
        return True

    elif isinstance(error, app_commands.MissingPermissions):
        # discord.py標準の権限不足
        perms_str = "、".join(error.missing_permissions)
        view = CommonErrorView(
            title="権限エラー",
            description=f"このコマンドを実行する権限がありません。\n必要な権限: {perms_str}"
        )
        await _send_error_response(interaction, view)
        return True

    # 未処理のエラー
    log_prefix = f"[{cog_name}] " if cog_name else ""
    logger.error(f"{log_prefix}コマンドエラー: {error}")
    view = CommonErrorView(
        title="エラー",
        description="コマンドの実行中にエラーが発生しました。"
    )
    await _send_error_response(interaction, view)
    return True


async def _send_error_response(
    interaction: discord.Interaction,
    view: ui.LayoutView
) -> None:
    """エラーレスポンスを送信（response/followup を適切に選択）"""
    if interaction.response.is_done():
        await interaction.followup.send(view=view, ephemeral=True)
    else:
        await interaction.response.send_message(view=view, ephemeral=True)
