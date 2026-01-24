"""
Rank コマンド
"""
from __future__ import annotations

from typing import Optional

import discord
from discord import app_commands, ui

from views.common_views import CommonInfoView


class RankView(ui.LayoutView):
    """ランク表示用View"""

    def __init__(
        self,
        target: discord.User,
        level: int,
        xp: int,
        text_rank: int,
        vc_level: int,
        vc_time: int,
        vc_rank: int,
        reactions_given: int = 0,
        reactions_received: int = 0
    ) -> None:
        super().__init__(timeout=300)

        next_level_xp = (level + 1) * 100

        text_progress = int((xp / next_level_xp) * 10) if next_level_xp > 0 else 10
        text_bar = "█" * text_progress + "░" * (10 - text_progress)
        text_percentage = int((xp / next_level_xp) * 100) if next_level_xp > 0 else 100

        vc_progress_seconds = vc_time % 3600
        vc_progress = int((vc_progress_seconds / 3600) * 10)
        vc_bar = "█" * vc_progress + "░" * (10 - vc_progress)
        vc_percentage = int((vc_progress_seconds / 3600) * 100)

        hours = vc_time // 3600
        minutes = (vc_time % 3600) // 60
        if hours > 0:
            vc_time_str = f"{hours}時間{minutes}分"
        elif minutes > 0:
            vc_time_str = f"{minutes}分"
        else:
            vc_time_str = "0分"

        container = ui.Container(accent_colour=discord.Colour.blurple())

        header_section = ui.Section(
            ui.TextDisplay(f"# {target.display_name} のステータス"),
            accessory=ui.Thumbnail(target.display_avatar.url)
        )
        container.add_item(header_section)
        container.add_item(ui.Separator())

        container.add_item(ui.TextDisplay(
            f"### 💬 テキストレベル\n"
            f"**Lv.{level}** (#{text_rank if text_rank else 'N/A'})\n"
            f"{xp} / {next_level_xp} XP\n"
            f"`{text_bar}` {text_percentage}%"
        ))

        container.add_item(ui.Separator())

        container.add_item(ui.TextDisplay(
            f"### 🎤 VCレベル\n"
            f"**Lv.{vc_level}** (#{vc_rank if vc_rank else 'N/A'})\n"
            f"合計: {vc_time_str}\n"
            f"`{vc_bar}` {vc_percentage}%"
        ))

        container.add_item(ui.Separator())

        container.add_item(ui.TextDisplay(
            f"### 😄 リアクション\n"
            f"つけた数: **{reactions_given:,}** 回\n"
            f"もらった数: **{reactions_received:,}** 回"
        ))

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# ユーザーID: {target.id}"))

        self.add_item(container)


class RankMixin:
    """Rank コマンド Mixin"""

    @app_commands.command(name="rank", description="レベルと経験値を表示します")
    @app_commands.describe(user="表示するユーザー（省略で自分）")
    async def rank(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.User] = None
    ) -> None:
        """ユーザーのレベルを表示"""
        target = user or interaction.user
        guild_id = interaction.guild.id

        # 一括取得（N+1クエリ対策）
        user_data = await self.db.get_user_level_with_ranks(guild_id, target.id)

        if not user_data:
            view = CommonInfoView(
                title="レベル情報",
                description=f"{target.mention} はまだレベルデータがありません。\nメッセージを送信またはVCに参加しましょう！"
            )
            await interaction.response.send_message(view=view)
            return

        view = RankView(
            target=target,
            level=user_data["level"],
            xp=user_data["xp"],
            text_rank=user_data.get("text_rank"),
            vc_level=user_data.get("vc_level", 0),
            vc_time=user_data.get("vc_time", 0),
            vc_rank=user_data.get("vc_rank"),
            reactions_given=user_data.get("reactions_given", 0),
            reactions_received=user_data.get("reactions_received", 0)
        )

        await interaction.response.send_message(view=view)
