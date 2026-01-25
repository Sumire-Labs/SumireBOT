"""
WordCounter イベントリスナー
"""
from __future__ import annotations

import discord
from discord.ext import commands

from utils.logging import get_logger

logger = get_logger("sumire.cogs.wordcounter.events")


class WordCounterEventsMixin:
    """WordCounter イベントリスナー Mixin"""

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """メッセージ内の単語をカウント"""
        # Bot・DM除外
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id

        # 設定を取得
        settings = await self.db.get_wordcounter_settings(guild_id)
        if not settings or not settings.get("enabled", True):
            return

        words = settings.get("words", [])
        if not words:
            return

        milestones = settings.get("milestones", [10, 50, 100, 200, 300, 500, 1000])

        for word in words:
            # 出現回数をカウント（大文字小文字区別）
            count = message.content.count(word)
            if count == 0:
                continue

            try:
                # カウント増加
                new_total = await self.db.increment_word_count(
                    guild_id, message.author.id, word, count
                )

                # マイルストーンチェック
                user_data = await self.db.get_user_word_count(
                    guild_id, message.author.id, word
                )
                last_milestone = user_data.get("last_milestone", 0) if user_data else 0

                # 達成したマイルストーンを確認
                for milestone in sorted(milestones):
                    if last_milestone < milestone <= new_total:
                        # 通知送信
                        await message.channel.send(
                            f"🎉 {message.author.mention} が「**{word}**」を **{milestone}回** 達成しました！",
                            allowed_mentions=discord.AllowedMentions(users=[message.author])
                        )
                        await self.db.update_last_milestone(
                            guild_id, message.author.id, word, milestone
                        )
                        break  # 1メッセージで1通知まで

                logger.debug(f"単語カウント: {word} x{count} by {message.author} (合計: {new_total})")

            except Exception as e:
                logger.error(f"単語カウントエラー: {e}")
