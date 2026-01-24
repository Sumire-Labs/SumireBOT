"""
Cog読み込み管理
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from utils.logging import get_logger

if TYPE_CHECKING:
    from discord.ext.commands import Bot

logger = get_logger("sumire.cog_loader")

# 読み込むCogのリスト
COGS = [
    "cogs.general",
    "cogs.utility",
    "cogs.ticket",
    "cogs.moderation",
    "cogs.music",
    "cogs.leveling",
    "cogs.admin",
    "cogs.giveaway",
    "cogs.poll",
    "cogs.star",
    "cogs.embedfix",
    "cogs.teamshuffle",
    "cogs.warthunder",
]


async def load_cogs(bot: Bot) -> tuple[int, int]:
    """
    全Cogを読み込む

    Args:
        bot: Botインスタンス

    Returns:
        tuple[int, int]: (成功数, 失敗数)
    """
    success_count = 0
    fail_count = 0

    for cog in COGS:
        try:
            await bot.load_extension(cog)
            logger.info(f"Cogを読み込みました: {cog}")
            success_count += 1
        except Exception as e:
            logger.error(f"Cogの読み込みに失敗: {cog} - {e}")
            fail_count += 1

    return success_count, fail_count


async def reload_cog(bot: Bot, cog_name: str) -> bool:
    """
    指定したCogをリロード

    Args:
        bot: Botインスタンス
        cog_name: Cog名（"cogs." プレフィックスなしでも可）

    Returns:
        bool: 成功した場合True
    """
    if not cog_name.startswith("cogs."):
        cog_name = f"cogs.{cog_name}"

    if cog_name not in COGS:
        logger.error(f"存在しないCog: {cog_name}")
        return False

    try:
        await bot.reload_extension(cog_name)
        logger.info(f"Cogをリロードしました: {cog_name}")
        return True
    except Exception as e:
        logger.error(f"Cogのリロードに失敗: {cog_name} - {e}")
        return False


async def reload_all_cogs(bot: Bot) -> tuple[int, int]:
    """
    全Cogをリロード

    Args:
        bot: Botインスタンス

    Returns:
        tuple[int, int]: (成功数, 失敗数)
    """
    success_count = 0
    fail_count = 0

    for cog in COGS:
        try:
            await bot.reload_extension(cog)
            success_count += 1
        except Exception as e:
            logger.error(f"Cogのリロードに失敗: {cog} - {e}")
            fail_count += 1

    logger.info(f"全Cogリロード完了: 成功={success_count}, 失敗={fail_count}")
    return success_count, fail_count


def get_cog_list() -> list[str]:
    """Cogリストを取得"""
    return COGS.copy()


def get_cog_names() -> list[str]:
    """Cog名のみのリストを取得（プレフィックスなし）"""
    return [cog.replace("cogs.", "") for cog in COGS]
