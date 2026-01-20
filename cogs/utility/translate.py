"""
翻訳コマンド
"""
from __future__ import annotations

from typing import Optional

import discord
from discord import app_commands, ui

from utils.logging import get_logger

try:
    from googletrans import Translator, LANGUAGES
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    LANGUAGES = {}

logger = get_logger("sumire.cogs.utility.translate")

# サポート言語の日本語名マッピング（主要なもの）
LANGUAGE_NAMES_JA = {
    "ja": "日本語",
    "en": "英語",
    "ko": "韓国語",
    "zh-cn": "中国語（簡体）",
    "zh-tw": "中国語（繁体）",
    "es": "スペイン語",
    "fr": "フランス語",
    "de": "ドイツ語",
    "it": "イタリア語",
    "pt": "ポルトガル語",
    "ru": "ロシア語",
    "ar": "アラビア語",
    "hi": "ヒンディー語",
    "th": "タイ語",
    "vi": "ベトナム語",
    "id": "インドネシア語",
    "ms": "マレー語",
    "tl": "タガログ語",
    "nl": "オランダ語",
    "pl": "ポーランド語",
    "tr": "トルコ語",
    "uk": "ウクライナ語",
    "cs": "チェコ語",
    "sv": "スウェーデン語",
    "da": "デンマーク語",
    "fi": "フィンランド語",
    "el": "ギリシャ語",
    "he": "ヘブライ語",
    "hu": "ハンガリー語",
    "no": "ノルウェー語",
    "ro": "ルーマニア語",
    "sk": "スロバキア語",
    "bg": "ブルガリア語",
    "hr": "クロアチア語",
    "lt": "リトアニア語",
    "lv": "ラトビア語",
    "et": "エストニア語",
    "sl": "スロベニア語",
}


def get_language_name(code: str) -> str:
    """言語コードから日本語名を取得"""
    if code in LANGUAGE_NAMES_JA:
        return LANGUAGE_NAMES_JA[code]
    if code in LANGUAGES:
        return LANGUAGES[code].title()
    return code


async def language_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    """言語のオートコンプリート"""
    choices = []

    # 主要言語を優先
    primary_langs = ["ja", "en", "ko", "zh-cn", "zh-tw", "es", "fr", "de"]

    for code in primary_langs:
        name = get_language_name(code)
        if current.lower() in name.lower() or current.lower() in code.lower():
            choices.append(app_commands.Choice(name=f"{name} ({code})", value=code))

    # その他の言語
    if LANGUAGES:
        for code, name in LANGUAGES.items():
            if code in primary_langs:
                continue
            ja_name = get_language_name(code)
            if current.lower() in ja_name.lower() or current.lower() in code.lower() or current.lower() in name.lower():
                choices.append(app_commands.Choice(name=f"{ja_name} ({code})", value=code))

            if len(choices) >= 25:
                break

    return choices[:25]


class TranslateResultView(ui.LayoutView):
    """翻訳結果表示用View (Components V2)"""

    def __init__(
        self,
        original_text: str,
        translated_text: str,
        source_lang: str,
        source_name: str,
        target_lang: str,
        target_name: str,
        requester: str
    ) -> None:
        super().__init__(timeout=300)

        container = ui.Container(accent_colour=discord.Colour.blue())

        # ヘッダー
        container.add_item(ui.TextDisplay("# 🌐 翻訳結果"))
        container.add_item(ui.TextDisplay(f"`{source_lang}` → `{target_lang}`"))
        container.add_item(ui.Separator())

        # 元のテキスト
        display_original = original_text if len(original_text) <= 500 else original_text[:497] + "..."
        container.add_item(ui.TextDisplay(f"**📝 元のテキスト ({source_name})**"))
        container.add_item(ui.TextDisplay(f"```\n{display_original}\n```"))

        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        # 翻訳結果
        display_translated = translated_text if len(translated_text) <= 500 else translated_text[:497] + "..."
        container.add_item(ui.TextDisplay(f"**📖 翻訳 ({target_name})**"))
        container.add_item(ui.TextDisplay(f"```\n{display_translated}\n```"))

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# リクエスト: {requester}"))

        self.add_item(container)


class TranslateErrorView(ui.LayoutView):
    """翻訳エラー表示用View (Components V2)"""

    def __init__(self, title: str, description: str) -> None:
        super().__init__(timeout=300)

        container = ui.Container(accent_colour=discord.Colour.red())

        container.add_item(ui.TextDisplay(f"# ❌ {title}"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(description))

        self.add_item(container)


class TranslateMixin:
    """翻訳コマンド Mixin"""

    def _init_translator(self) -> None:
        """翻訳機能の初期化"""
        if TRANSLATOR_AVAILABLE:
            self.translator = Translator()
        else:
            self.translator = None
            logger.warning("googletrans が利用できません。翻訳機能は無効です。")

    @app_commands.command(name="translate", description="テキストを翻訳します")
    @app_commands.describe(
        text="翻訳するテキスト",
        target="翻訳先の言語（省略時は日本語）"
    )
    @app_commands.autocomplete(target=language_autocomplete)
    async def translate(
        self,
        interaction: discord.Interaction,
        text: str,
        target: Optional[str] = None
    ) -> None:
        """テキストを翻訳するコマンド"""
        await interaction.response.defer()

        if not self.translator:
            view = TranslateErrorView(
                title="翻訳機能エラー",
                description="翻訳機能が利用できません。\n`googletrans-py` がインストールされているか確認してください。"
            )
            await interaction.followup.send(view=view)
            return

        # デフォルトの翻訳先言語
        target_lang = target or self.config.default_target_language

        # 言語コードの検証
        if target_lang not in LANGUAGES and target_lang not in ["zh-cn", "zh-tw"]:
            view = TranslateErrorView(
                title="無効な言語",
                description=f"`{target_lang}` は有効な言語コードではありません。\n言語を選択するか、有効な言語コードを入力してください。"
            )
            await interaction.followup.send(view=view)
            return

        # テキスト長チェック
        if len(text) > 2000:
            view = TranslateErrorView(
                title="テキストが長すぎます",
                description="翻訳するテキストは2000文字以内にしてください。"
            )
            await interaction.followup.send(view=view)
            return

        try:
            # 翻訳実行
            result = self.translator.translate(text, dest=target_lang)

            # 元の言語を取得
            source_lang = result.src
            source_name = get_language_name(source_lang)
            target_name = get_language_name(target_lang)

            # Components V2 Viewを作成
            view = TranslateResultView(
                original_text=text,
                translated_text=result.text,
                source_lang=source_lang,
                source_name=source_name,
                target_lang=target_lang,
                target_name=target_name,
                requester=str(interaction.user)
            )

            await interaction.followup.send(view=view)
            logger.debug(f"翻訳: {source_lang} → {target_lang} by {interaction.user}")

        except Exception as e:
            logger.error(f"翻訳エラー: {e}")
            view = TranslateErrorView(
                title="翻訳エラー",
                description="翻訳中にエラーが発生しました。\nしばらく待ってから再度お試しください。"
            )
            await interaction.followup.send(view=view)
