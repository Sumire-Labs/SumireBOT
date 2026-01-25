"""
Roll (ダイス) コマンド
"""
from __future__ import annotations

import random
import re

import discord
from discord import app_commands, ui


class RollResultView(ui.LayoutView):
    """ダイス結果表示用View (Components V2)"""

    def __init__(
        self,
        user: discord.User,
        dice_count: int,
        dice_sides: int,
        rolls: list[int],
        total: int
    ) -> None:
        super().__init__(timeout=300)

        container = ui.Container(accent_colour=discord.Colour.blue())
        container.add_item(ui.TextDisplay("# 🎲 ダイスロール"))
        container.add_item(ui.Separator())

        # ダイス表記
        dice_notation = f"{dice_count}d{dice_sides}" if dice_count > 1 else f"d{dice_sides}"

        # 結果表示
        if dice_count == 1:
            # 1個の場合はシンプルに
            result_text = f"**{dice_notation}** → **{total}**"
        elif dice_count <= 20:
            # 20個以下は全て表示
            rolls_str = " + ".join(str(r) for r in rolls)
            result_text = f"**{dice_notation}** → {rolls_str} = **{total}**"
        else:
            # 20個超は省略
            first_rolls = " + ".join(str(r) for r in rolls[:10])
            result_text = f"**{dice_notation}** → {first_rolls} + ... = **{total}**"

        container.add_item(ui.TextDisplay(result_text))

        # 統計情報（複数ダイスの場合）
        if dice_count > 1:
            avg = total / dice_count
            container.add_item(ui.TextDisplay(
                f"最小: {min(rolls)} / 最大: {max(rolls)} / 平均: {avg:.1f}"
            ))

        self.add_item(container)


class RollMixin:
    """ダイスコマンド Mixin"""

    @app_commands.command(name="roll", description="ダイスを振ります (例: 2d6, d20, 3d100)")
    @app_commands.describe(dice="ダイス表記 (例: 2d6, d20, 3d100)")
    async def roll(self, interaction: discord.Interaction, dice: str) -> None:
        """ダイスを振る"""
        # パース: NdM または dM 形式
        match = re.match(r'^(\d*)d(\d+)$', dice.lower().strip())

        if not match:
            await interaction.response.send_message(
                "❌ 無効な形式です。例: `2d6`, `d20`, `3d100`",
                ephemeral=True
            )
            return

        count_str, sides_str = match.groups()
        dice_count = int(count_str) if count_str else 1
        dice_sides = int(sides_str)

        # バリデーション
        if dice_count < 1 or dice_count > 100:
            await interaction.response.send_message(
                "❌ ダイスの数は1〜100個までです。",
                ephemeral=True
            )
            return

        if dice_sides < 2 or dice_sides > 10000:
            await interaction.response.send_message(
                "❌ ダイスの面数は2〜10000までです。",
                ephemeral=True
            )
            return

        # ダイスロール
        rolls = [random.randint(1, dice_sides) for _ in range(dice_count)]
        total = sum(rolls)

        view = RollResultView(
            user=interaction.user,
            dice_count=dice_count,
            dice_sides=dice_sides,
            rolls=rolls,
            total=total
        )

        await interaction.response.send_message(view=view)
