"""
Giveaway用 Components V2 View
"""
from __future__ import annotations

from typing import Optional
from datetime import datetime

import discord
from discord import ui

from utils.database import Database
from utils.logging import get_logger

logger = get_logger("sumire.views.giveaway")


class GiveawayView(ui.LayoutView):
    """アクティブなGiveaway View（永続的）"""

    def __init__(
        self,
        prize: str,
        host: discord.User | discord.Member,
        end_time: datetime,
        participant_count: int = 0,
        winner_count: int = 1
    ) -> None:
        super().__init__(timeout=None)  # 永続的View
        self.db = Database()

        container = ui.Container(accent_colour=discord.Colour.gold())

        # ヘッダー
        container.add_item(ui.TextDisplay("# 🎉 GIVEAWAY"))
        container.add_item(ui.Separator())

        # 情報
        end_timestamp = int(end_time.timestamp())
        container.add_item(ui.TextDisplay(
            f"**🎁 賞品:** {prize}\n"
            f"**👤 主催:** {host.mention}\n"
            f"**🏆 当選者数:** {winner_count}人\n"
            f"**⏰ 終了:** <t:{end_timestamp}:R>"
        ))
        container.add_item(ui.Separator())

        # 参加者数
        container.add_item(ui.TextDisplay(f"**👥 参加者:** {participant_count}人"))
        container.add_item(ui.Separator())

        # 参加ボタン
        button_row = ui.ActionRow()
        button_row.add_item(ui.Button(
            label="🎉 参加する",
            style=discord.ButtonStyle.success,
            custom_id="giveaway:join"
        ))
        container.add_item(button_row)

        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """インタラクションのチェックとルーティング"""
        custom_id = interaction.data.get("custom_id", "")

        if custom_id == "giveaway:join":
            await self.handle_join(interaction)
            return False

        return True

    async def handle_join(self, interaction: discord.Interaction) -> None:
        """参加処理"""
        message_id = interaction.message.id
        user_id = interaction.user.id

        # 参加者を追加
        added = await self.db.add_giveaway_participant(message_id, user_id)

        if added:
            await interaction.response.send_message(
                "🎉 Giveawayに参加しました！当選をお待ちください。",
                ephemeral=True
            )
            # 参加者数を更新
            giveaway = await self.db.get_giveaway(message_id)
            if giveaway:
                await self.update_view(interaction, giveaway)
        else:
            await interaction.response.send_message(
                "既に参加済みです。",
                ephemeral=True
            )

    async def update_view(
        self,
        interaction: discord.Interaction,
        giveaway: dict
    ) -> None:
        """View を更新"""
        host = interaction.guild.get_member(giveaway["host_id"])
        if not host:
            try:
                host = await interaction.client.fetch_user(giveaway["host_id"])
            except Exception:
                host = None

        end_time = datetime.fromisoformat(giveaway["end_time"])
        participant_count = len(giveaway["participants"])

        new_view = GiveawayView(
            prize=giveaway["prize"],
            host=host or interaction.user,
            end_time=end_time,
            participant_count=participant_count,
            winner_count=giveaway["winner_count"]
        )

        try:
            await interaction.message.edit(view=new_view)
        except Exception as e:
            logger.error(f"Giveaway View更新エラー: {e}")


class GiveawayEndedView(ui.LayoutView):
    """終了したGiveaway View"""

    def __init__(
        self,
        prize: str,
        winners: list[discord.User | discord.Member],
        participant_count: int,
        host: Optional[discord.User | discord.Member] = None
    ) -> None:
        super().__init__(timeout=None)  # 永続的View

        container = ui.Container(accent_colour=discord.Colour.green())

        # ヘッダー
        container.add_item(ui.TextDisplay("# 🎊 GIVEAWAY 終了"))
        container.add_item(ui.Separator())

        # 賞品
        container.add_item(ui.TextDisplay(f"**🎁 賞品:** {prize}"))

        # 当選者
        if winners:
            winner_mentions = ", ".join(w.mention for w in winners)
            container.add_item(ui.TextDisplay(f"**🏆 当選者:** {winner_mentions}"))
        else:
            container.add_item(ui.TextDisplay("**🏆 当選者:** なし（参加者がいませんでした）"))

        # 参加者数
        container.add_item(ui.TextDisplay(f"**👥 参加者:** {participant_count}人"))

        if host:
            container.add_item(ui.TextDisplay(f"**👤 主催:** {host.mention}"))

        self.add_item(container)


class GiveawayNoParticipantsView(ui.LayoutView):
    """参加者なしで終了したGiveaway View"""

    def __init__(self, prize: str) -> None:
        super().__init__(timeout=None)

        container = ui.Container(accent_colour=discord.Colour.greyple())

        container.add_item(ui.TextDisplay("# 🎉 GIVEAWAY 終了"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(
            f"**🎁 賞品:** {prize}\n\n"
            "参加者がいなかったため、当選者はいません。"
        ))

        self.add_item(container)
