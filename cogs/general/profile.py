"""
Profile コマンド
"""
from __future__ import annotations

import discord
from discord import app_commands

from utils.database import Database
from utils.logging import get_logger
from views.profile_views import ProfileView
from views.common_views import CommonErrorView

logger = get_logger("sumire.cogs.general.profile")


class ProfileMixin:
    """プロフィールコマンド Mixin"""

    @app_commands.command(name="profile", description="ユーザーのプロフィールを表示します")
    @app_commands.describe(user="表示するユーザー（省略で自分）")
    async def profile(
        self,
        interaction: discord.Interaction,
        user: discord.Member = None
    ) -> None:
        """ユーザープロフィールを表示"""
        if not interaction.guild:
            view = CommonErrorView(
                title="エラー",
                description="このコマンドはサーバー内でのみ使用できます。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # 対象ユーザー
        member = user or interaction.user

        # メンバーオブジェクトを取得（user引数がMemberでない場合に備えて）
        if not isinstance(member, discord.Member):
            member = interaction.guild.get_member(member.id)
            if not member:
                view = CommonErrorView(
                    title="エラー",
                    description="ユーザーが見つかりません。"
                )
                await interaction.response.send_message(view=view, ephemeral=True)
                return

        await interaction.response.defer()

        # データベースからアクティビティ統計を取得
        db = Database()
        user_data = await db.get_user_level(interaction.guild.id, member.id)

        vc_time = 0
        reactions_given = 0
        reactions_received = 0

        if user_data:
            vc_time = user_data.get("vc_time", 0)
            reactions_given = user_data.get("reactions_given", 0)
            reactions_received = user_data.get("reactions_received", 0)

        # プロフィールViewを作成
        view = ProfileView(
            member=member,
            vc_time=vc_time,
            reactions_given=reactions_given,
            reactions_received=reactions_received
        )

        await interaction.followup.send(view=view)
        logger.debug(f"Profile表示: {member} by {interaction.user}")
