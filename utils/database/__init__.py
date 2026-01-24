"""
データベースモジュール

Usage:
    from utils.database import Database

    db = Database()
    await db.connect("path/to/db.sqlite")
    await db.add_user_xp(guild_id, user_id, 10)
"""
from .core import DatabaseCore
from .guild import GuildMixin
from .logger import LoggerMixin
from .persistent import PersistentViewMixin
from .music import MusicMixin
from .autorole import AutoroleMixin
from .ticket import TicketMixin
from .leveling import LevelingMixin
from .giveaway import GiveawayMixin
from .poll import PollMixin
from .star import StarMixin
from .teamshuffle import TeamShuffleMixin


class Database(
    GuildMixin,
    LoggerMixin,
    PersistentViewMixin,
    MusicMixin,
    AutoroleMixin,
    TicketMixin,
    LevelingMixin,
    GiveawayMixin,
    PollMixin,
    StarMixin,
    TeamShuffleMixin,
    DatabaseCore,  # 最後に配置（MRO対策）
):
    """
    統合データベースクラス（シングルトン）

    全てのデータベース操作をこのクラスから行う。
    各機能はMixinとして分割されており、保守性が高い。

    Usage:
        db = Database()
        await db.connect("path/to/db.sqlite")

        # XP操作
        await db.add_user_xp(guild_id, user_id, 10)

        # トランザクション
        async with db.transaction():
            await db.add_user_xp(...)
            await db.add_reaction_given(...)
    """
    pass


__all__ = ["Database"]
