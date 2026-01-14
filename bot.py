"""
すみれBot v2 - メインエントリーポイント
Discord.py 2.6.4を使用した多機能Discord BOT
"""
from __future__ import annotations

import asyncio
import discord
import psutil
from discord.ext import commands, tasks

from utils.config import Config
from utils.database import Database
from utils.logging import setup_logging, get_logger


class SumireBot(commands.Bot):
    """すみれBot v2 メインクラス"""

    def __init__(self) -> None:
        self.config = Config()

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(
            command_prefix="!",  # スラッシュコマンド専用だが、prefixは必須
            intents=intents,
            description=self.config.description
        )

        self.db = Database()
        self.logger = get_logger("sumire")
        self._process = psutil.Process()

    async def setup_hook(self) -> None:
        """Bot起動時の初期化処理"""
        # データベース接続
        await self.db.connect(self.config.database_path)
        self.logger.info("データベースに接続しました")

        # Cogsの読み込み
        cogs = [
            "cogs.ping",
            "cogs.avatar",
            "cogs.logger",
            "cogs.ticket",
            "cogs.translate",
            "cogs.music",
            "cogs.autorole",
            "cogs.leveling",
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                self.logger.info(f"Cogを読み込みました: {cog}")
            except Exception as e:
                self.logger.error(f"Cogの読み込みに失敗: {cog} - {e}")

        # 永続的Viewの登録
        from views import PersistentViewManager
        await PersistentViewManager.register_all(self)
        self.logger.info("永続的Viewを登録しました")

        # スラッシュコマンドの同期
        await self.tree.sync()
        self.logger.info("スラッシュコマンドを同期しました")

    async def on_ready(self) -> None:
        """Bot準備完了時"""
        self.logger.info(f"ログイン完了: {self.user} (ID: {self.user.id})")
        self.logger.info(f"接続サーバー数: {len(self.guilds)}")

        # ステータス更新タスクを開始
        if not self.update_status.is_running():
            self.update_status.start()

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """サーバー参加時"""
        await self.db.ensure_guild(guild.id)
        self.logger.info(f"新しいサーバーに参加: {guild.name} (ID: {guild.id})")

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """サーバー退出時"""
        self.logger.info(f"サーバーから退出: {guild.name} (ID: {guild.id})")

    @tasks.loop(seconds=30)
    async def update_status(self) -> None:
        """ステータスを定期更新（CPU・メモリ使用量表示）"""
        try:
            # CPU使用率（Bot プロセスのみ）
            cpu_percent = self._process.cpu_percent()

            # メモリ使用量（Bot プロセスのみ、MB単位）
            memory_mb = self._process.memory_info().rss / 1024 / 1024

            # ステータス文字列
            status_text = f"CPU {cpu_percent:.1f}% | RAM {memory_mb:.0f}MB | {len(self.guilds)}サーバー"

            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name=status_text
            )
            await self.change_presence(activity=activity)

        except Exception as e:
            self.logger.error(f"ステータス更新エラー: {e}")

    @update_status.before_loop
    async def before_update_status(self) -> None:
        """ステータス更新タスク開始前にBotの準備を待つ"""
        await self.wait_until_ready()

    async def close(self) -> None:
        """Bot終了時のクリーンアップ"""
        self.logger.info("Botを終了します...")
        if self.update_status.is_running():
            self.update_status.cancel()
        await self.db.close()
        await super().close()


async def main() -> None:
    """メイン関数"""
    config = Config()

    # ロギング設定
    setup_logging(
        level=config.log_level,
        log_file=config.log_file,
        console=config.log_console
    )

    logger = get_logger("sumire")
    logger.info("すみれBot v2 を起動します...")

    # トークンチェック
    if not config.token or config.token == "YOUR_BOT_TOKEN_HERE":
        logger.error("BOTトークンが設定されていません。config.yaml を確認してください。")
        return

    # Bot起動
    bot = SumireBot()

    try:
        await bot.start(config.token)
    except discord.LoginFailure:
        logger.error("ログインに失敗しました。BOTトークンが正しいか確認してください。")
    except KeyboardInterrupt:
        pass  # Ctrl+C での終了は正常
    except asyncio.CancelledError:
        pass  # タスクキャンセルも正常
    finally:
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
