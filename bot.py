"""
すみれBot v2 - メインエントリーポイント
Discord.py 2.6.4を使用した多機能Discord BOT
"""
from __future__ import annotations

import asyncio
from typing import Optional

import discord
from discord.ext import commands

from utils.config import Config
from utils.database import Database
from utils.logging import setup_logging, get_logger
from utils.status import StatusManager
from utils.cog_loader import load_cogs


class SumireBot(commands.Bot):
    """すみれBot v2 メインクラス"""

    def __init__(self) -> None:
        self.config = Config()

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            description=self.config.description
        )

        self.db = Database()
        self.logger = get_logger("sumire")
        self.status_manager = StatusManager(self)

        # Web Dashboard
        self.web_app = None
        self.web_server: Optional[asyncio.Task] = None

    async def setup_hook(self) -> None:
        """Bot起動時の初期化処理"""
        # データベース接続
        await self.db.connect(self.config.database_path)
        self.logger.info("データベースに接続しました")

        # Cogsの読み込み
        await load_cogs(self)

        # 永続的Viewの登録
        from views import PersistentViewManager
        await PersistentViewManager.register_all(self)
        self.logger.info("永続的Viewを登録しました")

        # スラッシュコマンドの同期
        self.logger.info("スラッシュコマンドを同期中...")
        await self.tree.sync()
        self.logger.info("スラッシュコマンドを同期しました")

        # Web Dashboard初期化
        if self.config.web_enabled:
            from web import create_app
            self.web_app = create_app(self)
            self.logger.info("Web Dashboardを初期化しました")

    async def on_ready(self) -> None:
        """Bot準備完了時"""
        self.logger.info(f"ログイン完了: {self.user} (ID: {self.user.id})")
        self.logger.info(f"接続サーバー数: {len(self.guilds)}")

        # ステータス更新タスクを開始
        self.status_manager.start()

        # Web Dashboardを起動
        if self.config.web_enabled and self.web_app and self.web_server is None:
            self.web_server = asyncio.create_task(self._start_web_server())
            self.logger.info(
                f"Web Dashboard起動: http://{self.config.web_host}:{self.config.web_port}"
            )

    async def _start_web_server(self) -> None:
        """Webサーバーを起動"""
        import uvicorn

        config = uvicorn.Config(
            self.web_app,
            host=self.config.web_host,
            port=self.config.web_port,
            log_level="warning",  # uvicornのログは抑制
        )
        server = uvicorn.Server(config)
        await server.serve()

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """サーバー参加時"""
        await self.db.ensure_guild(guild.id)
        self.logger.info(f"新しいサーバーに参加: {guild.name} (ID: {guild.id})")

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """サーバー退出時"""
        self.logger.info(f"サーバーから退出: {guild.name} (ID: {guild.id})")

    async def close(self) -> None:
        """Bot終了時のクリーンアップ"""
        self.logger.info("Botを終了します...")

        # Web Dashboardを停止
        if self.web_server:
            self.web_server.cancel()
            try:
                await self.web_server
            except asyncio.CancelledError:
                pass
            self.logger.info("Web Dashboardを停止しました")

        self.status_manager.stop()
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
