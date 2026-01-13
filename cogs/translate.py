"""
翻訳機能 Cog
Google Translate (googletrans-py) を使用
"""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from utils.config import Config
from utils.embeds import EmbedBuilder
from utils.logging import get_logger

try:
    from googletrans import Translator, LANGUAGES
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    LANGUAGES = {}

logger = get_logger("sumire.cogs.translate")

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


# 言語選択用のオートコンプリート
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


class Translate(commands.Cog):
    """翻訳機能"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.config = Config()
        self.embed_builder = EmbedBuilder()

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
        """
        テキストを翻訳するコマンド
        """
        await interaction.response.defer()

        if not self.translator:
            embed = self.embed_builder.error(
                title="翻訳機能エラー",
                description="翻訳機能が利用できません。\n"
                           "`googletrans-py` がインストールされているか確認してください。"
            )
            await interaction.followup.send(embed=embed)
            return

        # デフォルトの翻訳先言語
        target_lang = target or self.config.default_target_language

        # 言語コードの検証
        if target_lang not in LANGUAGES and target_lang not in ["zh-cn", "zh-tw"]:
            embed = self.embed_builder.error(
                title="無効な言語",
                description=f"`{target_lang}` は有効な言語コードではありません。\n"
                           f"言語を選択するか、有効な言語コードを入力してください。"
            )
            await interaction.followup.send(embed=embed)
            return

        # テキスト長チェック
        if len(text) > 2000:
            embed = self.embed_builder.error(
                title="テキストが長すぎます",
                description="翻訳するテキストは2000文字以内にしてください。"
            )
            await interaction.followup.send(embed=embed)
            return

        try:
            # 翻訳実行
            result = self.translator.translate(text, dest=target_lang)

            # 元の言語を取得
            source_lang = result.src
            source_name = get_language_name(source_lang)
            target_name = get_language_name(target_lang)

            # 結果を整形
            embed = self.embed_builder.create(
                title="🌐 翻訳結果"
            )

            # 元のテキスト
            original_text = text if len(text) <= 1024 else text[:1021] + "..."
            embed.add_field(
                name=f"📝 元のテキスト ({source_name})",
                value=original_text,
                inline=False
            )

            # 翻訳結果
            translated_text = result.text if len(result.text) <= 1024 else result.text[:1021] + "..."
            embed.add_field(
                name=f"📖 翻訳 ({target_name})",
                value=translated_text,
                inline=False
            )

            # 言語情報
            embed.set_footer(text=f"{source_lang} → {target_lang} | リクエスト: {interaction.user}")

            await interaction.followup.send(embed=embed)
            logger.debug(f"翻訳: {source_lang} → {target_lang} by {interaction.user}")

        except Exception as e:
            logger.error(f"翻訳エラー: {e}")
            embed = self.embed_builder.error(
                title="翻訳エラー",
                description="翻訳中にエラーが発生しました。\n"
                           "しばらく待ってから再度お試しください。"
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="languages", description="サポートされている言語の一覧を表示します")
    async def languages(self, interaction: discord.Interaction) -> None:
        """
        サポートされている言語の一覧を表示
        """
        await interaction.response.defer(ephemeral=True)

        if not LANGUAGES:
            embed = self.embed_builder.error(
                title="言語一覧取得エラー",
                description="言語一覧を取得できませんでした。"
            )
            await interaction.followup.send(embed=embed)
            return

        # 主要言語
        primary = ["ja", "en", "ko", "zh-cn", "zh-tw", "es", "fr", "de", "it", "pt", "ru"]
        primary_list = []
        for code in primary:
            name = get_language_name(code)
            primary_list.append(f"`{code}` - {name}")

        embed = self.embed_builder.create(
            title="🌐 サポート言語一覧",
            description="翻訳でサポートされている言語の一覧です。"
        )

        embed.add_field(
            name="📌 主要言語",
            value="\n".join(primary_list),
            inline=False
        )

        # その他の言語数
        other_count = len(LANGUAGES) - len(primary)
        embed.add_field(
            name="📋 その他",
            value=f"その他 **{other_count}** 言語に対応しています。\n"
                  f"`/translate` コマンドで言語を入力すると候補が表示されます。",
            inline=False
        )

        embed.set_footer(text="言語コードを使用して翻訳先を指定できます")

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(Translate(bot))
