"""
Star 週間レポート自動送信
"""
from __future__ import annotations

from datetime import datetime, timedelta

import discord
from discord.ext import tasks

from utils.logging import get_logger
from views.star_views import StarLeaderboardView

logger = get_logger("sumire.cogs.star.weekly_report")


class StarWeeklyReportMixin:
    """Star 週間レポート自動送信 Mixin"""

    def start_weekly_report_task(self) -> None:
        """週間レポートタスクを開始"""
        self.check_weekly_reports.start()

    def stop_weekly_report_task(self) -> None:
        """週間レポートタスクを停止"""
        self.check_weekly_reports.cancel()

    @tasks.loop(hours=1)
    async def check_weekly_reports(self) -> None:
        """週間レポートを送信すべきサーバーをチェック"""
        try:
            guilds = await self.db.get_guilds_for_weekly_report()
            now = datetime.utcnow()

            for guild_data in guilds:
                guild_id = guild_data["guild_id"]
                channel_id = guild_data["weekly_report_channel_id"]
                last_sent = guild_data.get("weekly_report_last_sent")

                # 最終送信日時をチェック
                should_send = False
                if last_sent is None:
                    should_send = True
                else:
                    if isinstance(last_sent, str):
                        last_sent_dt = datetime.fromisoformat(last_sent)
                    else:
                        last_sent_dt = last_sent
                    # 7日以上経過していたら送信
                    if now - last_sent_dt >= timedelta(days=7):
                        should_send = True

                if should_send:
                    await self._send_weekly_report(guild_id, channel_id)

        except Exception as e:
            logger.error(f"週間レポートチェックエラー: {e}", exc_info=True)

    @check_weekly_reports.before_loop
    async def before_weekly_report_check(self) -> None:
        """タスク開始前にBotの準備を待つ"""
        await self.bot.wait_until_ready()

    async def _send_weekly_report(self, guild_id: int, channel_id: int) -> None:
        """週間レポートを送信"""
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                logger.warning(f"週間レポート: サーバーが見つかりません (ID: {guild_id})")
                return

            channel = guild.get_channel(channel_id)
            if not channel:
                logger.warning(f"週間レポート: チャンネルが見つかりません (ID: {channel_id})")
                return

            # 過去7日間のランキングを取得
            since = datetime.utcnow() - timedelta(days=7)
            message_rankings = await self.db.get_star_leaderboard(
                guild_id,
                limit=10,
                since=since
            )
            author_rankings = await self.db.get_author_star_totals(
                guild_id,
                limit=10,
                since=since
            )

            # データがない場合はスキップ
            if not message_rankings and not author_rankings:
                logger.debug(f"週間レポート: データなし (サーバー: {guild.name})")
                await self.db.update_weekly_report_last_sent(guild_id)
                return

            # レポートを送信（Components V2ではcontentは使用不可）
            view = StarLeaderboardView(
                guild=guild,
                message_rankings=message_rankings,
                author_rankings=author_rankings,
                period="weekly"
            )

            await channel.send(
                view=view,
                allowed_mentions=discord.AllowedMentions.none()
            )

            # 最終送信日時を更新
            await self.db.update_weekly_report_last_sent(guild_id)

            logger.info(f"週間レポート送信: {guild.name}")

        except discord.Forbidden:
            logger.warning(f"週間レポート: 送信権限なし (サーバー: {guild_id})")
        except Exception as e:
            logger.error(f"週間レポート送信エラー: {e}", exc_info=True)
