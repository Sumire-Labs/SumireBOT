"""
プロフィール用 Components V2 View
"""
from __future__ import annotations

from typing import Optional
from datetime import datetime

import discord
from discord import ui


def format_relative_time(dt: datetime) -> str:
    """相対時間を日本語で表示"""
    now = datetime.utcnow()
    diff = now - dt

    days = diff.days
    if days < 1:
        return "今日"
    elif days == 1:
        return "昨日"
    elif days < 7:
        return f"{days}日前"
    elif days < 30:
        weeks = days // 7
        return f"{weeks}週間前"
    elif days < 365:
        months = days // 30
        return f"{months}ヶ月前"
    else:
        years = days // 365
        return f"{years}年前"


def format_vc_time(seconds: int) -> str:
    """VC時間をフォーマット"""
    if seconds < 60:
        return f"{seconds}秒"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    if hours > 0:
        return f"{hours}時間{minutes}分"
    else:
        return f"{minutes}分"


def get_status_emoji(status: discord.Status) -> str:
    """ステータスの絵文字を取得"""
    status_map = {
        discord.Status.online: "🟢",
        discord.Status.idle: "🟡",
        discord.Status.dnd: "🔴",
        discord.Status.offline: "⚫",
        discord.Status.invisible: "⚫",
    }
    return status_map.get(status, "⚫")


def get_status_text(status: discord.Status) -> str:
    """ステータスのテキストを取得"""
    status_map = {
        discord.Status.online: "オンライン",
        discord.Status.idle: "退席中",
        discord.Status.dnd: "取り込み中",
        discord.Status.offline: "オフライン",
        discord.Status.invisible: "オフライン",
    }
    return status_map.get(status, "不明")


class ProfileView(ui.LayoutView):
    """ユーザープロフィール View"""

    def __init__(
        self,
        member: discord.Member,
        vc_time: int = 0,
        reactions_given: int = 0,
        reactions_received: int = 0
    ) -> None:
        super().__init__(timeout=300)

        container = ui.Container(accent_colour=member.accent_color or discord.Colour.blurple())

        # アバターとユーザー名（Sectionを使用）
        avatar_url = member.display_avatar.url

        # ヘッダー: ユーザー名
        header_text = f"# {member.display_name}"
        if member.display_name != member.name:
            header_text += f"\n@{member.name}"
        header_text += f"\n-# ID: {member.id}"

        section = ui.Section(
            accessory=ui.Thumbnail(media=avatar_url)
        )
        section.add_item(ui.TextDisplay(header_text))
        container.add_item(section)

        container.add_item(ui.Separator())

        # アカウント情報
        created_at = member.created_at.replace(tzinfo=None)
        joined_at = member.joined_at.replace(tzinfo=None) if member.joined_at else None

        created_date = created_at.strftime("%Y/%m/%d")
        created_relative = format_relative_time(created_at)

        account_info = f"### 📅 アカウント情報\n"
        account_info += f"**作成日:** {created_date} ({created_relative})\n"

        if joined_at:
            joined_date = joined_at.strftime("%Y/%m/%d")
            joined_relative = format_relative_time(joined_at)
            account_info += f"**参加日:** {joined_date} ({joined_relative})"

        container.add_item(ui.TextDisplay(account_info))
        container.add_item(ui.Separator())

        # ロール
        roles = [r for r in member.roles if r.name != "@everyone"]
        roles.reverse()  # 上位ロールを先に

        if roles:
            role_count = len(roles)
            # 最大10個まで表示
            display_roles = roles[:10]
            role_mentions = " ".join(r.mention for r in display_roles)

            role_text = f"### 🎭 ロール ({role_count}個)\n{role_mentions}"
            if role_count > 10:
                role_text += f"\n-# ...他 {role_count - 10}個"
        else:
            role_text = "### 🎭 ロール\nなし"

        container.add_item(ui.TextDisplay(role_text))
        container.add_item(ui.Separator())

        # アクティビティ統計
        activity_text = "### 📊 アクティビティ\n"
        activity_text += f"**🎤 VC累計:** {format_vc_time(vc_time)}\n"
        activity_text += f"**😄 リアクション:** {reactions_given:,}↑ / {reactions_received:,}↓"

        container.add_item(ui.TextDisplay(activity_text))
        container.add_item(ui.Separator())

        # ステータス
        status_emoji = get_status_emoji(member.status)
        status_text = get_status_text(member.status)

        status_line = f"### 🔰 ステータス\n{status_emoji} {status_text}"

        # アクティビティ（ゲーム、音楽など）
        if member.activities:
            for activity in member.activities:
                if isinstance(activity, discord.Game):
                    status_line += f" · 🎮 {activity.name}"
                    break
                elif isinstance(activity, discord.Streaming):
                    status_line += f" · 📺 配信中: {activity.name}"
                    break
                elif isinstance(activity, discord.Spotify):
                    status_line += f" · 🎵 {activity.title} - {activity.artist}"
                    break
                elif isinstance(activity, discord.CustomActivity):
                    if activity.name:
                        status_line += f" · {activity.name}"
                    break
                elif isinstance(activity, discord.Activity):
                    if activity.name:
                        activity_type_map = {
                            discord.ActivityType.playing: "🎮",
                            discord.ActivityType.watching: "👀",
                            discord.ActivityType.listening: "🎵",
                            discord.ActivityType.competing: "🏆",
                        }
                        emoji = activity_type_map.get(activity.type, "")
                        status_line += f" · {emoji} {activity.name}"
                        break

        container.add_item(ui.TextDisplay(status_line))

        self.add_item(container)
