"""
匿名告白用 Components V2 View
"""
from __future__ import annotations

import discord
from discord import ui


class ConfessView(ui.LayoutView):
    """匿名告白 View"""

    def __init__(self, content: str) -> None:
        super().__init__(timeout=None)

        container = ui.Container(accent_colour=discord.Colour.purple())

        # ヘッダー
        container.add_item(ui.TextDisplay("# 💭 匿名メッセージ"))
        container.add_item(ui.Separator())

        # 内容
        container.add_item(ui.TextDisplay(content))

        self.add_item(container)
