"""
メインAPIルーター
"""
from __future__ import annotations

from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "ok"}


@api_router.get("/info")
async def bot_info():
    """Bot情報を取得"""
    from fastapi import Request

    # TODO: Botの情報を返す
    return {
        "name": "SumireBot",
        "version": "2.0.0",
    }


# 認証ルーター
from web.api.auth import auth_router
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])

# ギルドルーター
from web.api.guilds import guilds_router
api_router.include_router(guilds_router, prefix="/guilds", tags=["guilds"])

# ランキングルーター
from web.api.leaderboards import leaderboards_router
api_router.include_router(leaderboards_router, prefix="/guilds/{guild_id}/leaderboard", tags=["leaderboards"])

# Giveawayルーター
from web.api.giveaways import giveaways_router
api_router.include_router(giveaways_router, prefix="/guilds/{guild_id}/giveaways", tags=["giveaways"])

# Pollルーター
from web.api.polls import polls_router
api_router.include_router(polls_router, prefix="/guilds/{guild_id}/polls", tags=["polls"])
