"""
永続的View管理
Bot再起動後もボタン等が動作するようにするための管理クラス
"""
from __future__ import annotations

import discord
from typing import TYPE_CHECKING

from utils.database import Database
from utils.logging import get_logger

if TYPE_CHECKING:
    from bot import SumireBot

logger = get_logger("sumire.views")


class PersistentViewManager:
    """永続的Viewを管理するクラス"""

    @staticmethod
    async def register_all(bot: SumireBot) -> None:
        """
        全ての永続的Viewをbotに登録
        Bot起動時に呼び出される
        """
        from .ticket_views import TicketPanelView, TicketControlView

        # チケットパネルView（custom_idベースで登録）
        bot.add_view(TicketPanelView(bot))

        # データベースから保存された永続的Viewを取得
        db = Database()

        # チケットコントロールパネルを復元
        ticket_controls = await db.get_persistent_views(view_type="ticket_control")
        for view_data in ticket_controls:
            try:
                ticket_id = view_data.get("data", {}).get("ticket_id")
                if ticket_id:
                    view = TicketControlView(bot, ticket_id)
                    bot.add_view(view, message_id=view_data["message_id"])
                    logger.debug(f"チケットコントロールViewを復元: message_id={view_data['message_id']}")
            except Exception as e:
                logger.error(f"View復元エラー: {e}")

        logger.info(f"永続的Viewを登録完了: {len(ticket_controls)} 個のチケットコントロール")

    @staticmethod
    async def save_view(
        guild_id: int,
        channel_id: int,
        message_id: int,
        view_type: str,
        data: dict = None
    ) -> None:
        """永続的Viewをデータベースに保存"""
        db = Database()
        await db.save_persistent_view(
            guild_id=guild_id,
            channel_id=channel_id,
            message_id=message_id,
            view_type=view_type,
            data=data
        )
        logger.debug(f"永続的Viewを保存: type={view_type}, message_id={message_id}")

    @staticmethod
    async def remove_view(message_id: int) -> None:
        """永続的Viewをデータベースから削除"""
        db = Database()
        await db.delete_persistent_view(message_id)
        logger.debug(f"永続的Viewを削除: message_id={message_id}")
