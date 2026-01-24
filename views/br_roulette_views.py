"""
War Thunder BRルーレット用 Components V2 View
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional

import discord
from discord import ui

from utils.logging import get_logger

if TYPE_CHECKING:
    from bot import SumireBot

logger = get_logger("sumire.views.br_roulette")

# BR範囲定義
BR_MAX = {
    "air": 14.3,
    "ground": 12.7
}

MODE_LABELS = {
    "air": "🛩️ 空",
    "ground": "🚛 陸"
}


def generate_br_list(mode: str) -> list[float]:
    """
    モードに応じたBRリストを生成

    Args:
        mode: "air" または "ground"

    Returns:
        BRのリスト (1.0, 1.3, 1.7, 2.0, ...)
    """
    max_br = BR_MAX.get(mode, 12.7)
    brs = []
    br = 1.0

    while br <= max_br + 0.01:  # 浮動小数点誤差対策
        brs.append(round(br, 1))
        # 1.0 → 1.3 → 1.7 → 2.0 パターン
        decimal = round(br % 1, 1)
        if decimal == 0.0:
            br += 0.3
        elif decimal == 0.3:
            br += 0.4
        else:  # 0.7
            br += 0.3

    return brs


def parse_exclusions(text: str, mode: str) -> tuple[list[float], list[str]]:
    """
    除外テキストをパースしてBRリストを返す

    Args:
        text: "1.0~2.7, 5.7, 10.0~14.3" 形式
        mode: "air" または "ground"

    Returns:
        tuple[除外BRリスト, 元の除外文字列リスト]
    """
    if not text.strip():
        return [], []

    all_brs = set(generate_br_list(mode))
    excluded_brs = set()
    exclusion_strs = []

    parts = [p.strip() for p in text.split(",")]

    for part in parts:
        if not part:
            continue

        if "~" in part:
            # 範囲指定 (例: 1.0~2.7)
            try:
                start_str, end_str = part.split("~")
                start = float(start_str.strip())
                end = float(end_str.strip())

                for br in all_brs:
                    if start <= br <= end:
                        excluded_brs.add(br)

                exclusion_strs.append(part.strip())
            except ValueError:
                continue
        else:
            # 単体指定 (例: 5.7)
            try:
                br = float(part)
                if br in all_brs:
                    excluded_brs.add(br)
                    exclusion_strs.append(part.strip())
            except ValueError:
                continue

    return sorted(excluded_brs), exclusion_strs


def spin_br(mode: str, excluded_brs: list[float]) -> Optional[float]:
    """
    ルーレット実行

    Args:
        mode: "air" または "ground"
        excluded_brs: 除外するBRリスト

    Returns:
        選ばれたBR、または利用可能なBRがない場合はNone
    """
    all_brs = generate_br_list(mode)
    excluded_set = set(excluded_brs)
    available = [br for br in all_brs if br not in excluded_set]

    if not available:
        return None

    return random.choice(available)


def format_br(br: float) -> str:
    """BRを文字列にフォーマット"""
    return f"{br:.1f}"


class ExclusionModal(ui.Modal, title="除外BR設定"):
    """BR除外設定用モーダル"""

    exclusion_input = ui.TextInput(
        label="除外するBR",
        placeholder="例: 1.0~2.7, 5.7, 10.0~14.3",
        style=discord.TextStyle.short,
        required=False,
        max_length=200
    )

    def __init__(self, view: "BRRouletteView", current_exclusions: str = "") -> None:
        super().__init__()
        self.view = view
        self.exclusion_input.default = current_exclusions

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """モーダル送信時"""
        text = self.exclusion_input.value

        # パース
        excluded_brs, exclusion_strs = parse_exclusions(text, self.view._mode)

        # 全BR除外チェック
        all_brs = generate_br_list(self.view._mode)
        if len(excluded_brs) >= len(all_brs):
            await interaction.response.send_message(
                "全てのBRを除外することはできません。",
                ephemeral=True
            )
            return

        # Viewを更新
        self.view._exclusion_text = ", ".join(exclusion_strs) if exclusion_strs else ""
        self.view._excluded_brs = excluded_brs
        self.view.clear_items()
        self.view._build_ui()

        await interaction.response.edit_message(view=self.view)


class BRRouletteView(ui.LayoutView):
    """BRルーレット View"""

    def __init__(
        self,
        bot: Optional[SumireBot] = None,
        mode: str = "air",
        current_br: Optional[float] = None,
        exclusion_text: str = "",
        excluded_brs: Optional[list[float]] = None,
        history: Optional[list[float]] = None
    ) -> None:
        super().__init__(timeout=None)  # 永続的View
        self.bot = bot
        self._mode = mode
        self._current_br = current_br
        self._exclusion_text = exclusion_text
        self._excluded_brs = excluded_brs or []
        self._history = history or []

        self._build_ui()

    def _build_ui(self) -> None:
        """UIを構築"""
        container = ui.Container(accent_colour=discord.Colour.orange())

        # ヘッダー
        container.add_item(ui.TextDisplay("# 🎰 BR ルーレット"))
        container.add_item(ui.Separator())

        # モード表示
        mode_label = MODE_LABELS.get(self._mode, "🛩️ 空")
        max_br = BR_MAX.get(self._mode, 12.7)
        container.add_item(ui.TextDisplay(f"**モード:** {mode_label} (1.0 ~ {max_br})"))
        container.add_item(ui.Separator())

        # 現在のBR
        if self._current_br is not None:
            container.add_item(ui.TextDisplay(f"# 【 {format_br(self._current_br)} 】"))
        else:
            container.add_item(ui.TextDisplay("### 🎲 ルーレットを回してください"))

        container.add_item(ui.Separator())

        # 除外BR表示
        if self._exclusion_text:
            container.add_item(ui.TextDisplay(f"**除外中:** {self._exclusion_text}"))
        else:
            container.add_item(ui.TextDisplay("**除外中:** なし"))

        # 履歴表示
        if self._history:
            history_str = " → ".join(format_br(br) for br in self._history[-5:])
            container.add_item(ui.TextDisplay(f"**📜 履歴:** {history_str}"))

        container.add_item(ui.Separator())

        # モード選択 Select Menu
        mode_row = ui.ActionRow()
        mode_row.add_item(ui.Select(
            placeholder="モード選択",
            options=[
                discord.SelectOption(
                    label="空",
                    value="air",
                    emoji="🛩️",
                    default=(self._mode == "air")
                ),
                discord.SelectOption(
                    label="陸",
                    value="ground",
                    emoji="🚛",
                    default=(self._mode == "ground")
                )
            ],
            custom_id="br:mode"
        ))
        container.add_item(mode_row)

        # ボタン行
        button_row = ui.ActionRow()
        button_row.add_item(ui.Button(
            label="🎰 ルーレット",
            style=discord.ButtonStyle.success,
            custom_id="br:spin"
        ))
        button_row.add_item(ui.Button(
            label="⚙️ 除外設定",
            style=discord.ButtonStyle.secondary,
            custom_id="br:exclude"
        ))
        container.add_item(button_row)

        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """インタラクションのチェックとルーティング"""
        custom_id = interaction.data.get("custom_id", "")

        if custom_id == "br:mode":
            await self.handle_mode_change(interaction)
            return False
        elif custom_id == "br:spin":
            await self.handle_spin(interaction)
            return False
        elif custom_id == "br:exclude":
            await self.handle_exclude(interaction)
            return False

        return True

    async def handle_mode_change(self, interaction: discord.Interaction) -> None:
        """モード変更処理"""
        values = interaction.data.get("values", [])
        if not values:
            return

        new_mode = values[0]

        if new_mode != self._mode:
            self._mode = new_mode
            # モード変更時は除外設定をリセット
            self._exclusion_text = ""
            self._excluded_brs = []
            self._current_br = None
            self._history = []

            self.clear_items()
            self._build_ui()

        await interaction.response.edit_message(view=self)

    async def handle_spin(self, interaction: discord.Interaction) -> None:
        """ルーレット実行"""
        result = spin_br(self._mode, self._excluded_brs)

        if result is None:
            await interaction.response.send_message(
                "利用可能なBRがありません。除外設定を確認してください。",
                ephemeral=True
            )
            return

        # 履歴に追加（最大5件）
        self._history.append(result)
        if len(self._history) > 5:
            self._history = self._history[-5:]

        self._current_br = result

        self.clear_items()
        self._build_ui()

        await interaction.response.edit_message(view=self)

    async def handle_exclude(self, interaction: discord.Interaction) -> None:
        """除外設定Modal表示"""
        modal = ExclusionModal(self, self._exclusion_text)
        await interaction.response.send_modal(modal)
