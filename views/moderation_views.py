"""
モデレーション用 Components V2 View
"""
from __future__ import annotations

import discord
from discord import ui
from typing import Optional


class LogModerationActionView(ui.LayoutView):
    """モデレーションアクションログ（ban/kick/timeout）"""

    def __init__(
        self,
        action_type: str,  # "ban", "kick", "timeout"
        target_name: str,
        target_mention: str,
        target_avatar: str,
        target_id: int,
        moderator_name: str,
        moderator_mention: str,
        reason: str,
        duration: Optional[str] = None  # timeout用
    ) -> None:
        super().__init__(timeout=None)

        # アクションタイプに応じた設定
        action_config = {
            "ban": {
                "colour": discord.Colour.dark_red(),
                "title": "## 🔨 ユーザーBAN",
                "desc": f"{target_mention} がBANされました"
            },
            "kick": {
                "colour": discord.Colour.orange(),
                "title": "## 👢 ユーザーキック",
                "desc": f"{target_mention} がキックされました"
            },
            "timeout": {
                "colour": discord.Colour.gold(),
                "title": "## ⏰ ユーザータイムアウト",
                "desc": f"{target_mention} がタイムアウトされました"
            }
        }

        config = action_config.get(action_type, action_config["kick"])
        container = ui.Container(accent_colour=config["colour"])

        # ヘッダー
        header = ui.Section(
            ui.TextDisplay(config["title"]),
            ui.TextDisplay(config["desc"]),
            accessory=ui.Thumbnail(target_avatar)
        )
        container.add_item(header)

        container.add_item(ui.Separator())

        # 詳細情報
        info_text = f"**対象ユーザー:** {target_name}\n"
        info_text += f"**実行者:** {moderator_mention}\n"
        info_text += f"**理由:** {reason}"

        if action_type == "timeout" and duration:
            info_text += f"\n**期間:** {duration}"

        container.add_item(ui.TextDisplay(info_text))

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# 対象ユーザーID: {target_id}"))

        self.add_item(container)


class ModerationSuccessView(ui.LayoutView):
    """モデレーション成功表示（コマンドレスポンス用）"""

    def __init__(
        self,
        action_type: str,  # "ban", "kick", "timeout"
        target_name: str,
        target_avatar: str,
        reason: str,
        duration: Optional[str] = None,
        dm_sent: bool = True
    ) -> None:
        super().__init__(timeout=None)

        action_text = {
            "ban": "BAN",
            "kick": "キック",
            "timeout": "タイムアウト"
        }

        container = ui.Container(accent_colour=discord.Colour.green())

        # ヘッダー
        header = ui.Section(
            ui.TextDisplay(f"## {action_text.get(action_type, action_type)}完了"),
            ui.TextDisplay(f"**{target_name}** を{action_text.get(action_type, action_type)}しました"),
            accessory=ui.Thumbnail(target_avatar)
        )
        container.add_item(header)

        container.add_item(ui.Separator())

        # 詳細
        info_text = f"**理由:** {reason}"
        if action_type == "timeout" and duration:
            info_text += f"\n**期間:** {duration}"

        container.add_item(ui.TextDisplay(info_text))

        # DM通知ステータス
        container.add_item(ui.Separator())
        if dm_sent:
            container.add_item(ui.TextDisplay("-# DM通知を送信しました"))
        else:
            container.add_item(ui.TextDisplay("-# DM通知の送信に失敗しました（処理は完了）"))

        self.add_item(container)


class ModerationDMView(ui.LayoutView):
    """モデレーション通知DM用"""

    def __init__(
        self,
        action_type: str,  # "ban", "kick", "timeout"
        guild_name: str,
        reason: str,
        duration: Optional[str] = None
    ) -> None:
        super().__init__(timeout=None)

        action_text = {
            "ban": ("BANされました", discord.Colour.dark_red()),
            "kick": ("キックされました", discord.Colour.orange()),
            "timeout": ("タイムアウトされました", discord.Colour.gold())
        }

        text, colour = action_text.get(action_type, ("処罰されました", discord.Colour.red()))
        container = ui.Container(accent_colour=colour)

        # ヘッダー
        container.add_item(ui.TextDisplay(f"## {guild_name}"))
        container.add_item(ui.TextDisplay(f"あなたはこのサーバーで**{text}**"))

        container.add_item(ui.Separator())

        # 理由
        info_text = f"**理由:** {reason}"
        if action_type == "timeout" and duration:
            info_text += f"\n**期間:** {duration}"

        container.add_item(ui.TextDisplay(info_text))

        self.add_item(container)
