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
        # 接続が閉じられている場合はスキップ
        if self.bot.is_closed() or self.bot.ws is None or self.bot.ws.socket is None:
            return

        try:
            # プロセスのメモリ使用量を別スレッドで取得
            mem_mb = await asyncio.to_thread(self._get_process_memory)

            # Discord API レイテンシ（ミリ秒）
            ping_ms = self.bot.latency * 1000

            # ステータス文字列
            status_text = f"RAM {mem_mb:.1f}MB | Ping {ping_ms:.0f}ms"

            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name=status_text
            )
            await self.bot.change_presence(activity=activity)
            logger.debug(f"ステータス更新: {status_text}")

        except (ConnectionResetError, OSError) as e:
            # 接続切断時のエラーは警告レベルで出力（トレースバックなし）
            logger.warning(f"ステータス更新スキップ（接続不安定）: {e}")
        except Exception as e:
            # 接続関連のエラーメッセージをチェック
            if "closing transport" in str(e).lower():
                logger.warning(f"ステータス更新スキップ（接続クローズ中）: {e}")
            else:
                logger.error(f"ステータス更新エラー: {e}", exc_info=True)

    @update_status.before_loop
    async def before_update_status(self) -> None:
        """ステータス更新タスク開始前にBotの準備を待つ"""
        await self.bot.wait_until_ready()

    @staticmethod
    def _get_process_memory() -> float:
        """プロセスのメモリ使用量を取得（同期関数）"""
        process = psutil.Process()
        mem_bytes = process.memory_info().rss
        mem_mb = mem_bytes / (1024 ** 2)
        return mem_mb
