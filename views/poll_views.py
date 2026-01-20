"""
投票用 Components V2 View
"""
from __future__ import annotations

from typing import Optional
from datetime import datetime

import discord
from discord import ui

from utils.database import Database
from utils.logging import get_logger

logger = get_logger("sumire.views.poll")

# 選択肢の絵文字
OPTION_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


def create_progress_bar(percentage: float, length: int = 10) -> str:
    """プログレスバーを作成"""
    filled = int(percentage / 100 * length)
    empty = length - filled
    return "█" * filled + "░" * empty


class PollView(ui.LayoutView):
    """アクティブな投票 View（永続的）"""

    def __init__(
        self,
        question: str,
        options: list[str],
        votes: dict[str, list[int]],
        multi_select: bool = False,
        end_time: Optional[datetime] = None,
        ended: bool = False
    ) -> None:
        super().__init__(timeout=None)  # 永続的View
        self.db = Database()

        # 投票数を集計
        vote_counts = [0] * len(options)
        for user_votes in votes.values():
            for option_idx in user_votes:
                if 0 <= option_idx < len(options):
                    vote_counts[option_idx] += 1

        total_votes = sum(vote_counts)

        container = ui.Container(
            accent_colour=discord.Colour.greyple() if ended else discord.Colour.blue()
        )

        # ヘッダー
        header = "# 📊 投票終了" if ended else "# 📊 投票"
        container.add_item(ui.TextDisplay(header))
        container.add_item(ui.Separator())

        # 質問
        container.add_item(ui.TextDisplay(f"**{question}**"))

        if multi_select:
            container.add_item(ui.TextDisplay("-# 複数選択可"))

        container.add_item(ui.Separator())

        # 選択肢と投票状況
        for idx, option in enumerate(options):
            emoji = OPTION_EMOJIS[idx] if idx < len(OPTION_EMOJIS) else f"{idx + 1}."
            count = vote_counts[idx]
            percentage = (count / total_votes * 100) if total_votes > 0 else 0
            bar = create_progress_bar(percentage)

            container.add_item(ui.TextDisplay(
                f"{emoji} **{option}**\n"
                f"{bar} {percentage:.0f}% ({count}票)"
            ))

        container.add_item(ui.Separator())

        # フッター
        voter_count = len(votes)
        footer_text = f"**投票者:** {voter_count}人 | **総投票数:** {total_votes}票"

        if end_time and not ended:
            end_timestamp = int(end_time.timestamp())
            footer_text += f" | **終了:** <t:{end_timestamp}:R>"

        container.add_item(ui.TextDisplay(footer_text))

        # ボタン（終了していない場合のみ）
        if not ended:
            # ボタンは1行に5個まで
            for row_start in range(0, len(options), 5):
                button_row = ui.ActionRow()
                for idx in range(row_start, min(row_start + 5, len(options))):
                    emoji = OPTION_EMOJIS[idx] if idx < len(OPTION_EMOJIS) else str(idx + 1)
                    button_row.add_item(ui.Button(
                        label=emoji,
                        style=discord.ButtonStyle.primary,
                        custom_id=f"poll:vote:{idx}"
                    ))
                container.add_item(button_row)

        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """インタラクションのチェックとルーティング"""
        custom_id = interaction.data.get("custom_id", "")

        if custom_id.startswith("poll:vote:"):
            option_idx = int(custom_id.split(":")[-1])
            await self.handle_vote(interaction, option_idx)
            return False

        return True

    async def handle_vote(self, interaction: discord.Interaction, option_idx: int) -> None:
        """投票処理"""
        message_id = interaction.message.id
        user_id = interaction.user.id

        # 投票
        success = await self.db.vote_poll(message_id, user_id, option_idx)

        if success:
            await interaction.response.send_message(
                "✅ 投票しました！",
                ephemeral=True
            )
            # Viewを更新
            poll = await self.db.get_poll(message_id)
            if poll:
                await self.update_view(interaction, poll)
        else:
            await interaction.response.send_message(
                "投票できませんでした。",
                ephemeral=True
            )

    async def update_view(
        self,
        interaction: discord.Interaction,
        poll: dict
    ) -> None:
        """View を更新"""
        end_time = None
        if poll.get("end_time"):
            end_time = datetime.fromisoformat(poll["end_time"])

        new_view = PollView(
            question=poll["question"],
            options=poll["options"],
            votes=poll["votes"],
            multi_select=bool(poll["multi_select"]),
            end_time=end_time,
            ended=bool(poll["ended"])
        )

        try:
            await interaction.message.edit(view=new_view)
        except Exception as e:
            logger.error(f"Poll View更新エラー: {e}")


class PollEndedView(ui.LayoutView):
    """終了した投票 View"""

    def __init__(
        self,
        question: str,
        options: list[str],
        votes: dict[str, list[int]]
    ) -> None:
        super().__init__(timeout=None)

        # 投票数を集計
        vote_counts = [0] * len(options)
        for user_votes in votes.values():
            for option_idx in user_votes:
                if 0 <= option_idx < len(options):
                    vote_counts[option_idx] += 1

        total_votes = sum(vote_counts)

        # 最多得票を特定
        max_votes = max(vote_counts) if vote_counts else 0
        winners = [i for i, count in enumerate(vote_counts) if count == max_votes]

        container = ui.Container(accent_colour=discord.Colour.green())

        # ヘッダー
        container.add_item(ui.TextDisplay("# 📊 投票終了"))
        container.add_item(ui.Separator())

        # 質問
        container.add_item(ui.TextDisplay(f"**{question}**"))
        container.add_item(ui.Separator())

        # 選択肢と投票状況（最多得票にマーク）
        for idx, option in enumerate(options):
            emoji = OPTION_EMOJIS[idx] if idx < len(OPTION_EMOJIS) else f"{idx + 1}."
            count = vote_counts[idx]
            percentage = (count / total_votes * 100) if total_votes > 0 else 0
            bar = create_progress_bar(percentage)

            # 最多得票にはクラウンマーク
            crown = " 👑" if idx in winners and total_votes > 0 else ""

            container.add_item(ui.TextDisplay(
                f"{emoji} **{option}**{crown}\n"
                f"{bar} {percentage:.0f}% ({count}票)"
            ))

        container.add_item(ui.Separator())

        # フッター
        voter_count = len(votes)
        container.add_item(ui.TextDisplay(
            f"**投票者:** {voter_count}人 | **総投票数:** {total_votes}票"
        ))

        self.add_item(container)
