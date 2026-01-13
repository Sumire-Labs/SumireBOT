"""
ログシステム用 Components V2 View
"""
from __future__ import annotations

import discord
from discord import ui
from typing import Optional, Union
from datetime import datetime


class LogMessageDeleteView(ui.LayoutView):
    """メッセージ削除ログ"""

    def __init__(
        self,
        author_name: str,
        author_avatar: str,
        author_id: int,
        channel_mention: str,
        content: str
    ) -> None:
        super().__init__(timeout=None)

        container = ui.Container(accent_colour=discord.Colour.red())

        # ヘッダー
        header = ui.Section(
            ui.TextDisplay("## 📝 メッセージ削除"),
            ui.TextDisplay(f"**チャンネル:** {channel_mention}"),
            accessory=ui.Thumbnail(author_avatar)
        )
        container.add_item(header)

        container.add_item(ui.Separator())

        # ユーザー情報
        container.add_item(ui.TextDisplay(f"**ユーザー:** {author_name}"))

        # 削除されたメッセージ
        container.add_item(ui.TextDisplay("**削除されたメッセージ:**"))
        display_content = content[:500] if content else "*内容なし*"
        container.add_item(ui.TextDisplay(f"```\n{display_content}\n```"))

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# ユーザーID: {author_id}"))

        self.add_item(container)


class LogMessageEditView(ui.LayoutView):
    """メッセージ編集ログ"""

    def __init__(
        self,
        author_name: str,
        author_avatar: str,
        author_id: int,
        channel_mention: str,
        jump_url: str,
        before_content: str,
        after_content: str
    ) -> None:
        super().__init__(timeout=None)

        container = ui.Container(accent_colour=discord.Colour.orange())

        # ヘッダー
        header = ui.Section(
            ui.TextDisplay("## 📝 メッセージ編集"),
            ui.TextDisplay(f"**チャンネル:** {channel_mention}\n[メッセージへジャンプ]({jump_url})"),
            accessory=ui.Thumbnail(author_avatar)
        )
        container.add_item(header)

        container.add_item(ui.Separator())

        # ユーザー情報
        container.add_item(ui.TextDisplay(f"**ユーザー:** {author_name}"))

        # 編集前
        container.add_item(ui.TextDisplay("**編集前:**"))
        before_display = before_content[:300] if before_content else "*内容なし*"
        container.add_item(ui.TextDisplay(f"```\n{before_display}\n```"))

        # 編集後
        container.add_item(ui.TextDisplay("**編集後:**"))
        after_display = after_content[:300] if after_content else "*内容なし*"
        container.add_item(ui.TextDisplay(f"```\n{after_display}\n```"))

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# ユーザーID: {author_id}"))

        self.add_item(container)


class LogMemberJoinView(ui.LayoutView):
    """メンバー参加ログ"""

    def __init__(
        self,
        member_name: str,
        member_mention: str,
        member_avatar: str,
        member_id: int,
        created_at: str,
        member_count: int
    ) -> None:
        super().__init__(timeout=None)

        container = ui.Container(accent_colour=discord.Colour.green())

        # ヘッダー
        header = ui.Section(
            ui.TextDisplay("## 👤 メンバー参加"),
            ui.TextDisplay(f"{member_mention} がサーバーに参加しました"),
            accessory=ui.Thumbnail(member_avatar)
        )
        container.add_item(header)

        container.add_item(ui.Separator())

        # 情報
        info_text = f"**ユーザー:** {member_name}\n"
        info_text += f"**アカウント作成:** {created_at}\n"
        info_text += f"**メンバー数:** {member_count}"
        container.add_item(ui.TextDisplay(info_text))

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# ユーザーID: {member_id}"))

        self.add_item(container)


class LogMemberLeaveView(ui.LayoutView):
    """メンバー退出ログ"""

    def __init__(
        self,
        member_name: str,
        member_mention: str,
        member_avatar: str,
        member_id: int,
        joined_at: str,
        roles: list[str]
    ) -> None:
        super().__init__(timeout=None)

        container = ui.Container(accent_colour=discord.Colour.red())

        # ヘッダー
        header = ui.Section(
            ui.TextDisplay("## 👤 メンバー退出"),
            ui.TextDisplay(f"{member_mention} がサーバーから退出しました"),
            accessory=ui.Thumbnail(member_avatar)
        )
        container.add_item(header)

        container.add_item(ui.Separator())

        # 情報
        info_text = f"**ユーザー:** {member_name}\n"
        info_text += f"**参加日:** {joined_at}"
        container.add_item(ui.TextDisplay(info_text))

        # ロール
        if roles:
            roles_text = ", ".join(roles[:15])
            if len(roles) > 15:
                roles_text += f" 他{len(roles) - 15}個"
            container.add_item(ui.TextDisplay(f"**所持していたロール:** {roles_text}"))

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# ユーザーID: {member_id}"))

        self.add_item(container)


class LogMemberBanView(ui.LayoutView):
    """メンバーBANログ"""

    def __init__(
        self,
        user_name: str,
        user_mention: str,
        user_avatar: str,
        user_id: int,
        is_unban: bool = False
    ) -> None:
        super().__init__(timeout=None)

        if is_unban:
            container = ui.Container(accent_colour=discord.Colour.green())
            title = "## 🔓 メンバーUnban"
            desc = f"{user_mention} のBANが解除されました"
        else:
            container = ui.Container(accent_colour=discord.Colour.dark_red())
            title = "## 🔨 メンバーBAN"
            desc = f"{user_mention} がBANされました"

        # ヘッダー
        header = ui.Section(
            ui.TextDisplay(title),
            ui.TextDisplay(desc),
            accessory=ui.Thumbnail(user_avatar)
        )
        container.add_item(header)

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"**ユーザー:** {user_name}"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# ユーザーID: {user_id}"))

        self.add_item(container)


class LogChannelView(ui.LayoutView):
    """チャンネル作成/削除ログ"""

    def __init__(
        self,
        channel_name: str,
        channel_type: str,
        channel_id: int,
        is_delete: bool = False,
        channel_mention: Optional[str] = None
    ) -> None:
        super().__init__(timeout=None)

        if is_delete:
            container = ui.Container(accent_colour=discord.Colour.red())
            title = "## 📢 チャンネル削除"
            desc = f"**チャンネル名:** {channel_name}"
        else:
            container = ui.Container(accent_colour=discord.Colour.green())
            title = "## 📢 チャンネル作成"
            desc = f"**チャンネル:** {channel_mention or channel_name}"

        container.add_item(ui.TextDisplay(title))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(desc))
        container.add_item(ui.TextDisplay(f"**タイプ:** {channel_type}"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# チャンネルID: {channel_id}"))

        self.add_item(container)


class LogRoleView(ui.LayoutView):
    """ロール作成/削除ログ"""

    def __init__(
        self,
        role_name: str,
        role_id: int,
        is_delete: bool = False,
        role_mention: Optional[str] = None,
        role_colour: Optional[discord.Colour] = None
    ) -> None:
        super().__init__(timeout=None)

        colour = role_colour or (discord.Colour.red() if is_delete else discord.Colour.green())
        container = ui.Container(accent_colour=colour)

        if is_delete:
            title = "## 🎭 ロール削除"
            desc = f"**ロール名:** {role_name}"
        else:
            title = "## 🎭 ロール作成"
            desc = f"**ロール:** {role_mention or role_name}"

        container.add_item(ui.TextDisplay(title))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(desc))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# ロールID: {role_id}"))

        self.add_item(container)


class LogBulkDeleteView(ui.LayoutView):
    """一括メッセージ削除ログ"""

    def __init__(
        self,
        message_count: int,
        channel_mention: str
    ) -> None:
        super().__init__(timeout=None)

        container = ui.Container(accent_colour=discord.Colour.red())

        container.add_item(ui.TextDisplay("## 📝 メッセージ一括削除"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(
            f"**削除数:** {message_count} 件\n"
            f"**チャンネル:** {channel_mention}"
        ))

        self.add_item(container)


class LogMemberTimeoutView(ui.LayoutView):
    """メンバータイムアウトログ"""

    def __init__(
        self,
        member_name: str,
        member_mention: str,
        member_avatar: str,
        member_id: int,
        is_remove: bool = False,
        timeout_until: Optional[str] = None
    ) -> None:
        super().__init__(timeout=None)

        if is_remove:
            container = ui.Container(accent_colour=discord.Colour.green())
            title = "## ⏰ タイムアウト解除"
            desc = f"{member_mention} のタイムアウトが解除されました"
        else:
            container = ui.Container(accent_colour=discord.Colour.orange())
            title = "## ⏰ メンバータイムアウト"
            desc = f"{member_mention} がタイムアウトされました"

        # ヘッダー
        header = ui.Section(
            ui.TextDisplay(title),
            ui.TextDisplay(desc),
            accessory=ui.Thumbnail(member_avatar)
        )
        container.add_item(header)

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"**ユーザー:** {member_name}"))

        if not is_remove and timeout_until:
            container.add_item(ui.TextDisplay(f"**解除予定:** {timeout_until}"))

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# ユーザーID: {member_id}"))

        self.add_item(container)


class LogChannelUpdateView(ui.LayoutView):
    """チャンネル更新ログ"""

    def __init__(
        self,
        channel_name: str,
        channel_mention: str,
        channel_id: int,
        changes: list[str]
    ) -> None:
        super().__init__(timeout=None)

        container = ui.Container(accent_colour=discord.Colour.orange())

        container.add_item(ui.TextDisplay("## 📢 チャンネル更新"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"**チャンネル:** {channel_mention}"))

        if changes:
            changes_text = "\n".join(changes)
            container.add_item(ui.TextDisplay(f"**変更内容:**\n{changes_text}"))

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# チャンネルID: {channel_id}"))

        self.add_item(container)


class LogRoleUpdateView(ui.LayoutView):
    """ロール更新ログ"""

    def __init__(
        self,
        role_name: str,
        role_mention: str,
        role_id: int,
        changes: list[str],
        role_colour: Optional[discord.Colour] = None
    ) -> None:
        super().__init__(timeout=None)

        colour = role_colour if role_colour and role_colour.value else discord.Colour.orange()
        container = ui.Container(accent_colour=colour)

        container.add_item(ui.TextDisplay("## 🎭 ロール更新"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"**ロール:** {role_mention}"))

        if changes:
            changes_text = "\n".join(changes)
            container.add_item(ui.TextDisplay(f"**変更内容:**\n{changes_text}"))

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# ロールID: {role_id}"))

        self.add_item(container)
