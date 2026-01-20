"""
汎用 Components V2 View
エラー、成功、警告、情報メッセージ用
"""
from __future__ import annotations

from typing import Optional

import discord
from discord import ui


class CommonErrorView(ui.LayoutView):
    """エラーメッセージ用View"""

    def __init__(
        self,
        title: str,
        description: str,
        footer: Optional[str] = None
    ) -> None:
        super().__init__(timeout=300)

        container = ui.Container(accent_colour=discord.Colour.red())
        container.add_item(ui.TextDisplay(f"# ❌ {title}"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(description))

        if footer:
            container.add_item(ui.Separator())
            container.add_item(ui.TextDisplay(f"-# {footer}"))

        self.add_item(container)


class CommonSuccessView(ui.LayoutView):
    """成功メッセージ用View"""

    def __init__(
        self,
        title: str,
        description: str,
        footer: Optional[str] = None
    ) -> None:
        super().__init__(timeout=300)

        container = ui.Container(accent_colour=discord.Colour.green())
        container.add_item(ui.TextDisplay(f"# ✅ {title}"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(description))

        if footer:
            container.add_item(ui.Separator())
            container.add_item(ui.TextDisplay(f"-# {footer}"))

        self.add_item(container)


class CommonWarningView(ui.LayoutView):
    """警告メッセージ用View"""

    def __init__(
        self,
        title: str,
        description: str,
        footer: Optional[str] = None
    ) -> None:
        super().__init__(timeout=300)

        container = ui.Container(accent_colour=discord.Colour.orange())
        container.add_item(ui.TextDisplay(f"# ⚠️ {title}"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(description))

        if footer:
            container.add_item(ui.Separator())
            container.add_item(ui.TextDisplay(f"-# {footer}"))

        self.add_item(container)


class CommonInfoView(ui.LayoutView):
    """情報メッセージ用View"""

    def __init__(
        self,
        title: str,
        description: str,
        footer: Optional[str] = None
    ) -> None:
        super().__init__(timeout=300)

        container = ui.Container(accent_colour=discord.Colour.blue())
        container.add_item(ui.TextDisplay(f"# ℹ️ {title}"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(description))

        if footer:
            container.add_item(ui.Separator())
            container.add_item(ui.TextDisplay(f"-# {footer}"))

        self.add_item(container)
