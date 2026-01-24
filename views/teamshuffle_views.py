"""
チーム分けくじ用 Components V2 View
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional

import discord
from discord import ui

from utils.database import Database
from utils.logging import get_logger

if TYPE_CHECKING:
    from bot import SumireBot

logger = get_logger("sumire.views.teamshuffle")


def shuffle_teams(participants: list[int], team_count: int) -> list[list[int]]:
    """
    参加者をランダムにチーム分け

    Args:
        participants: 参加者のユーザーIDリスト
        team_count: チーム数

    Returns:
        チームごとのユーザーIDリスト
    """
    shuffled = participants.copy()
    random.shuffle(shuffled)

    teams = [[] for _ in range(team_count)]
    for i, user_id in enumerate(shuffled):
        teams[i % team_count].append(user_id)

    return teams


class TeamShufflePanelView(ui.LayoutView):
    """チーム分けくじパネル View（永続的）"""

    def __init__(
        self,
        bot: Optional[SumireBot] = None,
        title: str = "チーム分けくじ",
        creator: Optional[discord.User | discord.Member] = None,
        participants: Optional[list[int]] = None,
        team_count: int = 2
    ) -> None:
        super().__init__(timeout=None)  # 永続的View
        self.bot = bot
        self.db = Database()
        self._title = title
        self._creator = creator
        self._participants = participants or []
        self._team_count = team_count

        self._build_ui()

    def _build_ui(self) -> None:
        """UIを構築"""
        container = ui.Container(accent_colour=discord.Colour.blue())

        # ヘッダー
        container.add_item(ui.TextDisplay(f"# 🎲 {self._title}"))
        container.add_item(ui.Separator())

        # 説明
        container.add_item(ui.TextDisplay("参加ボタンを押してチーム分けに参加しましょう！"))
        container.add_item(ui.Separator())

        # 参加者表示
        participant_count = len(self._participants)
        if participant_count > 0:
            if participant_count <= 20:
                # 20人以下ならメンション表示
                mentions = ", ".join(f"<@{uid}>" for uid in self._participants)
                container.add_item(ui.TextDisplay(f"**👥 参加者 ({participant_count}人)**\n{mentions}"))
            else:
                # 20人超なら人数のみ
                container.add_item(ui.TextDisplay(f"**👥 参加者:** {participant_count}人"))
        else:
            container.add_item(ui.TextDisplay("**👥 参加者:** まだいません"))

        container.add_item(ui.Separator())

        # 参加・退出ボタン
        button_row = ui.ActionRow()
        button_row.add_item(ui.Button(
            label="✋ 参加",
            style=discord.ButtonStyle.success,
            custom_id="teamshuffle:join"
        ))
        button_row.add_item(ui.Button(
            label="🚪 退出",
            style=discord.ButtonStyle.secondary,
            custom_id="teamshuffle:leave"
        ))
        container.add_item(button_row)

        # チーム数選択
        select_row = ui.ActionRow()
        select_row.add_item(ui.Select(
            placeholder=f"📊 チーム数: {self._team_count}",
            options=[
                discord.SelectOption(
                    label=f"{i}チーム",
                    value=str(i),
                    default=(i == self._team_count)
                )
                for i in range(2, 11)  # 2〜10チーム
            ],
            custom_id="teamshuffle:teamcount"
        ))
        container.add_item(select_row)

        # シャッフル実行ボタン
        shuffle_row = ui.ActionRow()
        shuffle_row.add_item(ui.Button(
            label="🎲 シャッフル実行",
            style=discord.ButtonStyle.primary,
            custom_id="teamshuffle:shuffle"
        ))
        container.add_item(shuffle_row)

        # フッター
        if self._creator:
            container.add_item(ui.Separator())
            container.add_item(ui.TextDisplay(f"-# 作成者: {self._creator.mention} のみシャッフル実行可能"))

        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """インタラクションのチェックとルーティング"""
        custom_id = interaction.data.get("custom_id", "")

        if custom_id == "teamshuffle:join":
            await self.handle_join(interaction)
            return False
        elif custom_id == "teamshuffle:leave":
            await self.handle_leave(interaction)
            return False
        elif custom_id == "teamshuffle:teamcount":
            await self.handle_team_count(interaction)
            return False
        elif custom_id == "teamshuffle:shuffle":
            await self.handle_shuffle(interaction)
            return False

        return True

    async def handle_join(self, interaction: discord.Interaction) -> None:
        """参加処理"""
        message_id = interaction.message.id
        user_id = interaction.user.id

        added = await self.db.add_team_shuffle_participant(message_id, user_id)

        if added:
            await interaction.response.send_message(
                "✋ チーム分けくじに参加しました！",
                ephemeral=True
            )
            await self._update_view(interaction)
        else:
            await interaction.response.send_message(
                "既に参加済みです。",
                ephemeral=True
            )

    async def handle_leave(self, interaction: discord.Interaction) -> None:
        """退出処理"""
        message_id = interaction.message.id
        user_id = interaction.user.id

        removed = await self.db.remove_team_shuffle_participant(message_id, user_id)

        if removed:
            await interaction.response.send_message(
                "🚪 チーム分けくじから退出しました。",
                ephemeral=True
            )
            await self._update_view(interaction)
        else:
            await interaction.response.send_message(
                "参加していません。",
                ephemeral=True
            )

    async def handle_team_count(self, interaction: discord.Interaction) -> None:
        """チーム数変更処理"""
        message_id = interaction.message.id
        values = interaction.data.get("values", [])

        if not values:
            return

        new_count = int(values[0])

        # パネル情報を取得して作成者チェック
        panel = await self.db.get_team_shuffle_panel(message_id)
        if not panel:
            await interaction.response.send_message(
                "パネルが見つかりません。",
                ephemeral=True
            )
            return

        if interaction.user.id != panel["creator_id"]:
            await interaction.response.send_message(
                "チーム数を変更できるのは作成者のみです。",
                ephemeral=True
            )
            return

        await self.db.update_team_shuffle_team_count(message_id, new_count)
        await interaction.response.send_message(
            f"📊 チーム数を {new_count} に変更しました。",
            ephemeral=True
        )
        await self._update_view(interaction)

    async def handle_shuffle(self, interaction: discord.Interaction) -> None:
        """シャッフル実行処理"""
        message_id = interaction.message.id

        # パネル情報を取得
        panel = await self.db.get_team_shuffle_panel(message_id)
        if not panel:
            await interaction.response.send_message(
                "パネルが見つかりません。",
                ephemeral=True
            )
            return

        # 作成者チェック
        if interaction.user.id != panel["creator_id"]:
            await interaction.response.send_message(
                "シャッフルを実行できるのは作成者のみです。",
                ephemeral=True
            )
            return

        participants = panel["participants"]
        team_count = panel["team_count"]

        # 参加者チェック
        if len(participants) < 2:
            await interaction.response.send_message(
                "シャッフルには最低2人の参加者が必要です。",
                ephemeral=True
            )
            return

        if len(participants) < team_count:
            await interaction.response.send_message(
                f"参加者数({len(participants)}人)がチーム数({team_count})より少ないです。\n"
                "チーム数を減らすか、参加者を増やしてください。",
                ephemeral=True
            )
            return

        # シャッフル実行
        teams = shuffle_teams(participants, team_count)

        # 結果Viewを作成
        result_view = TeamShuffleResultView(
            title=panel["title"],
            teams=teams,
            creator=interaction.user,
            guild=interaction.guild
        )

        # 元のメッセージを削除
        try:
            await interaction.message.delete()
        except Exception as e:
            logger.error(f"パネル削除エラー: {e}")

        # DBから削除
        await self.db.delete_team_shuffle_panel(message_id)

        # 結果を送信
        await interaction.response.send_message(view=result_view)

    async def _update_view(self, interaction: discord.Interaction) -> None:
        """Viewを更新"""
        message_id = interaction.message.id
        panel = await self.db.get_team_shuffle_panel(message_id)

        if not panel:
            return

        # 作成者を取得
        creator = interaction.guild.get_member(panel["creator_id"])
        if not creator:
            try:
                creator = await interaction.client.fetch_user(panel["creator_id"])
            except Exception:
                creator = None

        # 新しいViewを作成
        new_view = TeamShufflePanelView(
            bot=self.bot,
            title=panel["title"],
            creator=creator,
            participants=panel["participants"],
            team_count=panel["team_count"]
        )

        try:
            await interaction.message.edit(view=new_view)
        except Exception as e:
            logger.error(f"View更新エラー: {e}")


class TeamShuffleResultView(ui.LayoutView):
    """チーム分け結果 View（静的）"""

    def __init__(
        self,
        title: str,
        teams: list[list[int]],
        creator: discord.User | discord.Member,
        guild: Optional[discord.Guild] = None
    ) -> None:
        super().__init__(timeout=300)  # 5分後にタイムアウト

        container = ui.Container(accent_colour=discord.Colour.green())

        # ヘッダー
        container.add_item(ui.TextDisplay(f"# 🎲 {title} - 結果"))
        container.add_item(ui.Separator())

        # 各チームを表示
        total_participants = sum(len(team) for team in teams)
        for i, team in enumerate(teams, 1):
            if team:
                mentions = ", ".join(f"<@{uid}>" for uid in team)
                container.add_item(ui.TextDisplay(f"### 📋 チーム{i}\n{mentions}"))
            else:
                container.add_item(ui.TextDisplay(f"### 📋 チーム{i}\n-# メンバーなし"))

        container.add_item(ui.Separator())

        # フッター
        container.add_item(ui.TextDisplay(
            f"**実行者:** {creator.mention}\n"
            f"**参加者:** {total_participants}人 → {len(teams)}チーム"
        ))

        self.add_item(container)
