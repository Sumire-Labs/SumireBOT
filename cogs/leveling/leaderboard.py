"""
Leaderboard コマンド
"""
from __future__ import annotations

import discord
from discord import app_commands, ui

from views.common_views import CommonInfoView


class LeaderboardView(ui.LayoutView):
    """ランキング表示用View"""

    def __init__(
        self,
        guild: discord.Guild,
        text_leaderboard: list[dict],
        vc_leaderboard: list[dict]
    ) -> None:
        super().__init__(timeout=300)

        medals = ["🥇", "🥈", "🥉"]

        container = ui.Container(accent_colour=discord.Colour.gold())

        if guild.icon:
            header_section = ui.Section(
                ui.TextDisplay(f"# 🏆 サーバーランキング\n**{guild.name}** のトップ10"),
                accessory=ui.Thumbnail(guild.icon.url)
            )
            container.add_item(header_section)
        else:
            container.add_item(ui.TextDisplay(f"# 🏆 サーバーランキング\n**{guild.name}** のトップ10"))

        container.add_item(ui.Separator())

        if text_leaderboard:
            text_ranking = ""
            for idx, data in enumerate(text_leaderboard, 1):
                medal = medals[idx - 1] if idx <= 3 else f"**{idx}.**"
                text_ranking += f"{medal} <@{data['user_id']}> Lv.**{data['level']}**\n"
            container.add_item(ui.TextDisplay(f"### 💬 テキストランキング\n{text_ranking}"))
        else:
            container.add_item(ui.TextDisplay("### 💬 テキストランキング\nデータなし"))

        container.add_item(ui.Separator())

        if vc_leaderboard:
            vc_ranking = ""
            for idx, data in enumerate(vc_leaderboard, 1):
                medal = medals[idx - 1] if idx <= 3 else f"**{idx}.**"
                vc_ranking += f"{medal} <@{data['user_id']}> Lv.**{data['vc_level']}**\n"
            container.add_item(ui.TextDisplay(f"### 🎤 VCランキング\n{vc_ranking}"))
        else:
            container.add_item(ui.TextDisplay("### 🎤 VCランキング\nデータなし"))

        self.add_item(container)


class LeaderboardMixin:
    """Leaderboard コマンド Mixin"""

    @app_commands.command(name="leaderboard", description="サーバーのレベルランキングを表示します")
    async def leaderboard(self, interaction: discord.Interaction) -> None:
        """サーバーのランキングを表示"""
        guild_id = interaction.guild.id
        text_leaderboard = await self.db.get_leaderboard(guild_id, limit=10)
        vc_leaderboard = await self.db.get_vc_leaderboard(guild_id, limit=10)

        if not text_leaderboard and not vc_leaderboard:
            view = CommonInfoView(
                title="ランキング",
                description="まだランキングデータがありません。\nメッセージを送信またはVCに参加しましょう！"
            )
            await interaction.response.send_message(view=view)
            return

        view = LeaderboardView(
            guild=interaction.guild,
            text_leaderboard=text_leaderboard,
            vc_leaderboard=vc_leaderboard
        )

        await interaction.response.send_message(
            view=view,
            allowed_mentions=discord.AllowedMentions.none()
        )
