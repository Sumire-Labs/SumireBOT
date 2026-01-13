"""
パーミッションチェックユーティリティ
"""
from __future__ import annotations

import discord
from discord import app_commands
from typing import Callable, TypeVar
from functools import wraps

T = TypeVar("T")


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
