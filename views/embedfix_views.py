"""
埋め込み修正用 Components V2 View
"""
from __future__ import annotations

from typing import Optional

import discord
from discord import ui

from utils.logging import get_logger

logger = get_logger("sumire.views.embedfix")


class EmbedFixView(ui.LayoutView):
    """埋め込み修正View"""

    def __init__(
        self,
        original_user_id: int,
        platform: str,
        fixed_url: str,
        original_url: str
    ) -> None:
        super().__init__(timeout=None)  # 永続的View
        self.original_user_id = original_user_id

        # プラットフォームごとの設定
        platform_config = {
            "twitter": {"emoji": "🐦", "name": "Twitter/X", "color": discord.Colour.from_rgb(29, 161, 242)},
            "instagram": {"emoji": "📸", "name": "Instagram", "color": discord.Colour.from_rgb(225, 48, 108)},
            "tiktok": {"emoji": "🎵", "name": "TikTok", "color": discord.Colour.from_rgb(0, 0, 0)},
            "reddit": {"emoji": "🤖", "name": "Reddit", "color": discord.Colour.from_rgb(255, 69, 0)},
            "threads": {"emoji": "🧵", "name": "Threads", "color": discord.Colour.from_rgb(0, 0, 0)},
            "bluesky": {"emoji": "🦋", "name": "Bluesky", "color": discord.Colour.from_rgb(0, 133, 255)},
            "pixiv": {"emoji": "🎨", "name": "Pixiv", "color": discord.Colour.from_rgb(0, 150, 250)},
        }

        config = platform_config.get(platform, {"emoji": "🔗", "name": platform.title(), "color": discord.Colour.blurple()})

        container = ui.Container(accent_colour=config["color"])

        # ヘッダー
        container.add_item(ui.TextDisplay(f"{config['emoji']} **{config['name']}** 埋め込み修正"))
        container.add_item(ui.Separator())

        # 修正されたURL
        container.add_item(ui.TextDisplay(fixed_url))

        # ボタン行
        button_row = ui.ActionRow()
        button_row.add_item(ui.Button(
            label="削除",
            style=discord.ButtonStyle.danger,
            custom_id=f"embedfix:delete:{original_user_id}",
            emoji="🗑️"
        ))
        container.add_item(button_row)

        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """インタラクションのチェック"""
        custom_id = interaction.data.get("custom_id", "")

        if custom_id.startswith("embedfix:delete:"):
            # 元の投稿者のみ削除可能
            allowed_user_id = int(custom_id.split(":")[-1])
            if interaction.user.id == allowed_user_id or interaction.user.guild_permissions.manage_messages:
                await interaction.message.delete()
            else:
                await interaction.response.send_message(
                    "この埋め込みは投稿者のみ削除できます。",
                    ephemeral=True
                )
            return False

        return True
