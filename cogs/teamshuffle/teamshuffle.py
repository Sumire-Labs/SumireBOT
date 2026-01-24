"""
チーム分けくじコマンド
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands

from utils.database import Database
from views.teamshuffle_views import TeamShufflePanelView

if TYPE_CHECKING:
    from bot import SumireBot


class TeamShuffleMixin:
    """チーム分けくじコマンド Mixin"""

    bot: SumireBot
    db: Database

    @app_commands.command(name="teamshuffle", description="チーム分けくじパネルを作成します")
    @app_commands.describe(title="パネルのタイトル（省略可）")
    @app_commands.guild_only()
    async def teamshuffle(
        self,
        interaction: discord.Interaction,
        title: str = "チーム分けくじ"
    ) -> None:
        """チーム分けくじパネルを作成"""
        # パネルViewを作成
        panel_view = TeamShufflePanelView(
            bot=self.bot,
            title=title,
            creator=interaction.user,
            participants=[],
            team_count=2
        )

        # パネルを送信
        await interaction.response.send_message(view=panel_view)

        # 送信したメッセージを取得
        message = await interaction.original_response()

        # DBに保存
        await self.db.create_team_shuffle_panel(
            guild_id=interaction.guild.id,
            channel_id=interaction.channel.id,
            message_id=message.id,
            creator_id=interaction.user.id,
            title=title
        )
