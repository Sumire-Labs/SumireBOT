"""
URL短縮コマンド (X.gd)
"""
from __future__ import annotations

import aiohttp
import re

import discord
from discord import app_commands, ui

from utils.logging import get_logger

logger = get_logger("sumire.cogs.utility.shorturl")

# URLバリデーション用の正規表現
URL_PATTERN = re.compile(
    r'^https?://'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)


class ShortUrlResultView(ui.LayoutView):
    """URL短縮結果表示用View (Components V2)"""

    def __init__(self, original_url: str, short_url: str) -> None:
        super().__init__(timeout=300)

        container = ui.Container(accent_colour=discord.Colour.green())
        container.add_item(ui.TextDisplay("# 🔗 URL短縮完了"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(
            f"**短縮URL:**\n{short_url}"
        ))
        container.add_item(ui.TextDisplay(
            f"**元のURL:**\n||{original_url}||"
        ))
        self.add_item(container)


class ShortUrlErrorView(ui.LayoutView):
    """URL短縮エラー表示用View (Components V2)"""

    def __init__(self, message: str) -> None:
        super().__init__(timeout=300)

        container = ui.Container(accent_colour=discord.Colour.red())
        container.add_item(ui.TextDisplay("# ❌ URL短縮エラー"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(message))
        self.add_item(container)


class ShortUrlMixin:
    """URL短縮コマンド Mixin"""

    @app_commands.command(name="short", description="URLを短縮します (X.gd)")
    @app_commands.describe(url="短縮したいURL")
    async def short(self, interaction: discord.Interaction, url: str) -> None:
        """URLを短縮"""
        # URLバリデーション
        if not URL_PATTERN.match(url):
            view = ShortUrlErrorView("無効なURLです。http:// または https:// で始まるURLを入力してください。")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # APIキー取得
        api_key = self.config.get("shorturl", {}).get("api_key", "")
        if not api_key:
            view = ShortUrlErrorView("URL短縮機能が設定されていません。管理者にお問い合わせください。")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "url": url,
                    "key": api_key
                }
                async with session.get(
                    "https://xgd.io/V1/shorten",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.error(f"X.gd API error: status={response.status}")
                        view = ShortUrlErrorView(f"APIエラーが発生しました。(ステータス: {response.status})")
                        await interaction.followup.send(view=view, ephemeral=True)
                        return

                    data = await response.json()

                    if "shorturl" not in data:
                        error_msg = data.get("message", "不明なエラー")
                        logger.error(f"X.gd API error: {error_msg}")
                        view = ShortUrlErrorView(f"短縮に失敗しました: {error_msg}")
                        await interaction.followup.send(view=view, ephemeral=True)
                        return

                    short_url = data["shorturl"]
                    view = ShortUrlResultView(original_url=url, short_url=short_url)
                    await interaction.followup.send(view=view)

                    logger.info(f"URL短縮: {url} -> {short_url}")

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error during URL shortening: {e}")
            view = ShortUrlErrorView("通信エラーが発生しました。しばらく待ってからお試しください。")
            await interaction.followup.send(view=view, ephemeral=True)
        except Exception as e:
            logger.error(f"Unexpected error during URL shortening: {e}", exc_info=True)
            view = ShortUrlErrorView("予期しないエラーが発生しました。")
            await interaction.followup.send(view=view, ephemeral=True)
