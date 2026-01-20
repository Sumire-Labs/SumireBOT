"""
システムステータス更新機能
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import discord
import psutil
from discord.ext import tasks

from utils.logging import get_logger

if TYPE_CHECKING:
    from discord.ext.commands import Bot

logger = get_logger("sumire.status")


class StatusManager:
    """システムステータス管理クラス"""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self._task_started = False

    def start(self) -> None:
        """ステータス更新タスクを開始"""
        if not self._task_started:
            self.update_status.start()
            self._task_started = True

    def stop(self) -> None:
        """ステータス更新タスクを停止"""
        if self._task_started and self.update_status.is_running():
            self.update_status.cancel()
            self._task_started = False

    @tasks.loop(seconds=5)
    async def update_status(self) -> None:
        """ステータスを定期更新（システムモニター表示）"""
        try:
            # システム情報を別スレッドで取得
            system_cpu, mem_used, mem_total = await asyncio.to_thread(self._get_system_stats)

            # Discord API レイテンシ（ミリ秒）
            ping_ms = self.bot.latency * 1000

            # ステータス文字列
            status_text = f"CPU {system_cpu:.0f}% | RAM {mem_used:.1f}/{mem_total:.0f}GB | Ping {ping_ms:.0f}ms"

            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name=status_text
            )
            await self.bot.change_presence(activity=activity)
            logger.debug(f"ステータス更新: {status_text}")

        except Exception as e:
            logger.error(f"ステータス更新エラー: {e}", exc_info=True)

    @update_status.before_loop
    async def before_update_status(self) -> None:
        """ステータス更新タスク開始前にBotの準備を待つ"""
        await self.bot.wait_until_ready()

    @staticmethod
    def _get_system_stats() -> tuple[float, float, float]:
        """システム統計を取得（同期関数）"""
        cpu = psutil.cpu_percent(interval=1.0)
        mem = psutil.virtual_memory()
        mem_used_gb = mem.used / (1024 ** 3)
        mem_total_gb = mem.total / (1024 ** 3)
        return cpu, mem_used_gb, mem_total_gb
