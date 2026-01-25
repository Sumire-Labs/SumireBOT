"""
WordCounter ランキングコマンド
"""
from __future__ import annotations

import discord
from discord import app_commands

from utils.logging import get_logger
from views.common_views import CommonErrorView, CommonInfoView
from views.wordcounter_views import WordCounterLeaderboardView, WordCounterMyCountView

logger = get_logger("sumire.cogs.wordcounter.leaderboard")


class WordCounterLeaderboardMixin:
    """WordCounter ランキングコマンド Mixin"""

    @app_commands.command(name="counterboard", description="単語カウンターのランキングを表示します")
    @app_commands.describe(word="ランキングを表示する単語（省略で全体）")
    async def counterboard(
        self,
        interaction: discord.Interaction,
        word: str = None
    ) -> None:
        """単語カウンターランキングを表示"""
        if not interaction.guild:
            view = CommonErrorView(
                title="エラー",
                description="このコマンドはサーバー内でのみ使用できます。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # 設定を取得して登録済み単語を確認
        settings = await self.db.get_wordcounter_settings(interaction.guild.id)
        registered_words = settings.get("words", []) if settings else []

        if word:
            # 特定の単語のランキング
            if word not in registered_words:
                view = CommonErrorView(
                    title="エラー",
                    description=f"「{word}」は登録されていない単語です。"
                )
                await interaction.response.send_message(view=view, ephemeral=True)
                return

            rankings = await self.db.get_word_leaderboard(
                interaction.guild.id,
                word,
                limit=10
            )

            if not rankings:
                view = CommonInfoView(
                    title="単語カウンター",
                    description=f"「{word}」のデータがまだありません。"
                )
                await interaction.response.send_message(view=view, ephemeral=True)
                return

            view = WordCounterLeaderboardView(
                guild=interaction.guild,
                word=word,
                rankings=rankings
            )
        else:
            # 全体ランキング
            rankings = await self.db.get_all_words_leaderboard(
                interaction.guild.id,
                limit=10
            )

            if not rankings:
                view = CommonInfoView(
                    title="単語カウンター",
                    description="まだデータがありません。"
                )
                await interaction.response.send_message(view=view, ephemeral=True)
                return

            view = WordCounterLeaderboardView(
                guild=interaction.guild,
                word=None,
                rankings=rankings
            )

        await interaction.response.send_message(
            view=view,
            allowed_mentions=discord.AllowedMentions.none()
        )

    @app_commands.command(name="mycount", description="自分の単語カウントを表示します")
    async def mycount(self, interaction: discord.Interaction) -> None:
        """自分の単語カウントを表示"""
        if not interaction.guild:
            view = CommonErrorView(
                title="エラー",
                description="このコマンドはサーバー内でのみ使用できます。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        counts = await self.db.get_user_word_totals(
            interaction.guild.id,
            interaction.user.id
        )

        if not counts:
            view = CommonInfoView(
                title="マイカウント",
                description="まだカウントデータがありません。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        view = WordCounterMyCountView(
            user=interaction.user,
            counts=counts
        )

        await interaction.response.send_message(view=view, ephemeral=True)
