"""
FastAPI アプリケーション
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from utils.config import Config
from utils.logging import get_logger

if TYPE_CHECKING:
    from bot import SumireBot

logger = get_logger("sumire.web")


def create_app(bot: SumireBot) -> FastAPI:
    """FastAPIアプリケーションを作成"""
    config = Config()

    app = FastAPI(
        title="SumireBot Dashboard",
        description="すみれBot v2 Web Dashboard API",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Botとデータベースの参照を保存
    app.state.bot = bot
    app.state.db = bot.db
    app.state.config = config

    # CORS設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.web_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # APIルーターを登録
    _register_routers(app)

    # 静的ファイル配信（フロントエンドビルド済みファイル）
    frontend_path = Path(__file__).parent.parent / "frontend" / "out"
    if frontend_path.exists():
        app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
        logger.info(f"フロントエンド静的ファイルをマウント: {frontend_path}")
    else:
        logger.warning(f"フロントエンドビルドが見つかりません: {frontend_path}")

    @app.on_event("startup")
    async def on_startup():
        logger.info("Web Dashboard API 起動")

    @app.on_event("shutdown")
    async def on_shutdown():
        logger.info("Web Dashboard API 終了")

    return app


def _register_routers(app: FastAPI) -> None:
    """APIルーターを登録"""
    from web.api.router import api_router

    app.include_router(api_router, prefix="/api")
