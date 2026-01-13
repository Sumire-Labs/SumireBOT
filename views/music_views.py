"""
音楽プレイヤー用 Components V2 View
"""
from __future__ import annotations

import discord
from discord import ui
from typing import Optional


class NowPlayingView(ui.LayoutView):
    """Now Playing 表示"""

    def __init__(
        self,
        title: str,
        author: str,
        duration: str,
        source: str,
        queue_count: int = 0,
        loop_mode: Optional[str] = None,
        thumbnail_url: Optional[str] = None
    ) -> None:
        super().__init__(timeout=None)

        container = ui.Container(accent_colour=discord.Colour.green())

        # ヘッダー
        header_section = ui.Section(
            ui.TextDisplay("## ▶️ Now Playing"),
            ui.TextDisplay(f"**{title}**"),
        )
        if thumbnail_url:
            header_section.accessory = ui.Thumbnail(thumbnail_url)
        container.add_item(header_section)

        container.add_item(ui.Separator())

        # 曲情報
        info_text = f"🎤 **アーティスト:** {author}\n"
        info_text += f"⏱️ **長さ:** {duration}\n"
        info_text += f"📡 **ソース:** {source}"
        container.add_item(ui.TextDisplay(info_text))

        # キューとループ情報
        if queue_count > 0 or loop_mode:
            container.add_item(ui.Separator())
            extra_text = ""
            if queue_count > 0:
                extra_text += f"📋 **キュー:** 残り {queue_count} 曲\n"
            if loop_mode and loop_mode != "off":
                loop_text = "🔂 トラック" if loop_mode == "track" else "🔁 キュー"
                extra_text += f"**ループ:** {loop_text}"
            container.add_item(ui.TextDisplay(extra_text.strip()))

        self.add_item(container)


class TrackRequestView(ui.LayoutView):
    """再生リクエスト表示"""

    def __init__(
        self,
        title: str,
        duration: str,
        source: str,
        thumbnail_url: Optional[str] = None
    ) -> None:
        super().__init__(timeout=None)

        container = ui.Container(accent_colour=discord.Colour.blue())

        # ヘッダー
        header_section = ui.Section(
            ui.TextDisplay("## 🎵 再生リクエスト"),
            ui.TextDisplay(f"**{title}**"),
        )
        if thumbnail_url:
            header_section.accessory = ui.Thumbnail(thumbnail_url)
        container.add_item(header_section)

        container.add_item(ui.Separator())

        # 情報
        info_text = f"⏱️ **長さ:** {duration}\n"
        info_text += f"📡 **ソース:** {source}"
        container.add_item(ui.TextDisplay(info_text))

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay("-# 再生が開始されると「Now Playing」が表示されます"))

        self.add_item(container)


class QueueAddView(ui.LayoutView):
    """キュー追加表示"""

    def __init__(
        self,
        title: str,
        duration: str,
        source: str,
        position: int,
        thumbnail_url: Optional[str] = None
    ) -> None:
        super().__init__(timeout=None)

        container = ui.Container(accent_colour=discord.Colour.green())

        # ヘッダー
        header_section = ui.Section(
            ui.TextDisplay("## ✅ キューに追加"),
            ui.TextDisplay(f"**{title}**"),
        )
        if thumbnail_url:
            header_section.accessory = ui.Thumbnail(thumbnail_url)
        container.add_item(header_section)

        container.add_item(ui.Separator())

        # 情報
        info_text = f"📍 **位置:** #{position}\n"
        info_text += f"⏱️ **長さ:** {duration}\n"
        info_text += f"📡 **ソース:** {source}"
        container.add_item(ui.TextDisplay(info_text))

        self.add_item(container)


class PlaylistAddView(ui.LayoutView):
    """プレイリスト追加表示"""

    def __init__(
        self,
        playlist_name: str,
        track_count: int,
        total_duration: str,
        source: str,
        first_track: Optional[str] = None,
        queue_count: int = 0,
        is_album: bool = False,
        thumbnail_url: Optional[str] = None,
        is_playing: bool = False
    ) -> None:
        super().__init__(timeout=None)

        container = ui.Container(accent_colour=discord.Colour.purple())

        type_text = "アルバム" if is_album else "プレイリスト"

        # ヘッダー
        header_section = ui.Section(
            ui.TextDisplay(f"## 📋 {type_text}を追加"),
            ui.TextDisplay(f"**{playlist_name}**"),
        )
        if thumbnail_url:
            header_section.accessory = ui.Thumbnail(thumbnail_url)
        container.add_item(header_section)

        container.add_item(ui.Separator())

        # 情報
        info_text = f"🎵 **曲数:** {track_count} 曲\n"
        info_text += f"⏱️ **総時間:** {total_duration}\n"
        info_text += f"📡 **ソース:** {source}"
        container.add_item(ui.TextDisplay(info_text))

        # 追加情報
        if first_track or queue_count > 0:
            container.add_item(ui.Separator())
            extra_text = ""
            if first_track:
                extra_text += f"▶️ **最初の曲:** {first_track}\n"
            if queue_count > 0:
                extra_text += f"📋 **キュー:** 残り {queue_count} 曲"
            container.add_item(ui.TextDisplay(extra_text.strip()))

        if is_playing:
            container.add_item(ui.Separator())
            container.add_item(ui.TextDisplay("-# 再生が開始されると「Now Playing」が表示されます"))

        self.add_item(container)


class MusicErrorView(ui.LayoutView):
    """エラー表示"""

    def __init__(
        self,
        title: str,
        description: str,
        hint: Optional[str] = None
    ) -> None:
        super().__init__(timeout=None)

        container = ui.Container(accent_colour=discord.Colour.red())

        # ヘッダー
        container.add_item(ui.TextDisplay(f"## ❌ {title}"))
        container.add_item(ui.Separator())

        # 説明
        container.add_item(ui.TextDisplay(description))

        # ヒント
        if hint:
            container.add_item(ui.Separator())
            container.add_item(ui.TextDisplay(f"💡 **ヒント:** {hint}"))

        self.add_item(container)


class MusicWarningView(ui.LayoutView):
    """警告表示"""

    def __init__(
        self,
        title: str,
        description: str,
        footer: Optional[str] = None
    ) -> None:
        super().__init__(timeout=None)

        container = ui.Container(accent_colour=discord.Colour.orange())

        # ヘッダー
        container.add_item(ui.TextDisplay(f"## ⚠️ {title}"))
        container.add_item(ui.Separator())

        # 説明
        container.add_item(ui.TextDisplay(description))

        # フッター
        if footer:
            container.add_item(ui.Separator())
            container.add_item(ui.TextDisplay(f"-# {footer}"))

        self.add_item(container)


class MusicSuccessView(ui.LayoutView):
    """成功表示"""

    def __init__(
        self,
        title: str,
        description: str
    ) -> None:
        super().__init__(timeout=None)

        container = ui.Container(accent_colour=discord.Colour.green())

        # ヘッダー
        container.add_item(ui.TextDisplay(f"## ✅ {title}"))
        container.add_item(ui.Separator())

        # 説明
        container.add_item(ui.TextDisplay(description))

        self.add_item(container)


class MusicInfoView(ui.LayoutView):
    """情報表示"""

    def __init__(
        self,
        title: str,
        description: str
    ) -> None:
        super().__init__(timeout=None)

        container = ui.Container(accent_colour=discord.Colour.blue())

        # ヘッダー
        container.add_item(ui.TextDisplay(f"## ℹ️ {title}"))
        container.add_item(ui.Separator())

        # 説明
        container.add_item(ui.TextDisplay(description))

        self.add_item(container)
