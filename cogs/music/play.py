"""
Play コマンド
"""
from __future__ import annotations

import re
from typing import Optional

import discord
import wavelink
from discord import app_commands

from utils.logging import get_logger
from views.music_views import (
    TrackRequestView,
    QueueAddView,
    PlaylistAddView,
    MusicErrorView,
)

logger = get_logger("sumire.cogs.music.play")

# Spotify URL 正規表現（/intl-ja/ などのロケールプレフィックスに対応）
SPOTIFY_REGEX = re.compile(
    r"https?://open\.spotify\.com/(?:intl-[a-z]{2}/)?(track|album|playlist)/([a-zA-Z0-9]+)"
)

# YouTube URL 正規表現
YOUTUBE_REGEX = re.compile(
    r"https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/playlist\?list=|music\.youtube\.com/watch\?v=)([a-zA-Z0-9_-]+)"
)

# SoundCloud URL 正規表現
SOUNDCLOUD_REGEX = re.compile(
    r"https?://(?:www\.)?soundcloud\.com/.+"
)


class PlayMixin:
    """Play コマンド Mixin"""

    async def _search_tracks(self, query: str) -> tuple[list[wavelink.Playable], Optional[str], Optional[str]]:
        """
        曲を検索

        Returns:
            tuple: (トラックリスト, プレイリスト名またはNone, タイプ "track"|"playlist"|"album"|None)
        """
        # Spotify URL の処理
        spotify_match = SPOTIFY_REGEX.match(query)
        if spotify_match:
            spotify_type = spotify_match.group(1)
            try:
                logger.info(f"Spotify {spotify_type} 検索: {query}")
                result = await wavelink.Playable.search(query)

                if isinstance(result, wavelink.Playlist):
                    tracks = list(result.tracks)
                    playlist_name = result.name or f"Spotify {spotify_type}"
                    logger.info(f"プレイリスト取得: {playlist_name} ({len(tracks)}曲)")
                    return (tracks, playlist_name, spotify_type)

                if result:
                    tracks = result if isinstance(result, list) else [result]
                    return (tracks[:1], None, "track")

            except Exception as e:
                logger.warning(f"Spotify検索エラー: {e}")
                return ([], None, None)

        # YouTube URL の処理
        youtube_match = YOUTUBE_REGEX.match(query)
        if youtube_match or "youtube.com" in query or "youtu.be" in query:
            try:
                logger.info(f"YouTube URL: {query}")
                result = await wavelink.Playable.search(query)

                if isinstance(result, wavelink.Playlist):
                    tracks = list(result.tracks)
                    playlist_name = result.name or "YouTube Playlist"
                    logger.info(f"YouTubeプレイリスト取得: {playlist_name} ({len(tracks)}曲)")
                    return (tracks, playlist_name, "playlist")

                if result:
                    tracks = result if isinstance(result, list) else [result]
                    logger.info(f"YouTube動画: {tracks[0].title}")
                    return (tracks[:1], None, "track")

            except Exception as e:
                logger.warning(f"YouTube読み込みエラー: {e}")
                return ([], None, None)

        # SoundCloud URL の処理
        if SOUNDCLOUD_REGEX.match(query):
            try:
                logger.info(f"SoundCloud URL: {query}")
                result = await wavelink.Playable.search(query)

                if isinstance(result, wavelink.Playlist):
                    tracks = list(result.tracks)
                    playlist_name = result.name or "SoundCloud Playlist"
                    return (tracks, playlist_name, "playlist")

                if result:
                    tracks = result if isinstance(result, list) else [result]
                    return (tracks[:1], None, "track")

            except Exception as e:
                logger.warning(f"SoundCloud読み込みエラー: {e}")
                return ([], None, None)

        # テキスト検索
        search_sources = [
            ("YouTube", wavelink.TrackSource.YouTube),
            ("YouTubeMusic", wavelink.TrackSource.YouTubeMusic),
        ]

        for source_name, source in search_sources:
            try:
                logger.info(f"{source_name}検索: {query}")
                result = await wavelink.Playable.search(query, source=source)
                if result:
                    tracks = result if isinstance(result, list) else [result]
                    logger.info(f"{source_name}で見つかりました: {tracks[0].title}")
                    return (tracks[:1], None, "track")
            except Exception as e:
                logger.warning(f"{source_name}検索エラー: {e}")
                continue

        # 最終フォールバック: SoundCloud
        try:
            logger.info(f"SoundCloud検索: {query}")
            result = await wavelink.Playable.search(f"scsearch:{query}")
            if result:
                tracks = result if isinstance(result, list) else [result]
                logger.info(f"SoundCloudで見つかりました: {tracks[0].title}")
                return (tracks[:1], None, "track")
        except Exception as e:
            logger.warning(f"SoundCloud検索エラー: {e}")

        return ([], None, None)

    async def _handle_playlist(
        self,
        interaction: discord.Interaction,
        player: wavelink.Player,
        tracks: list[wavelink.Playable],
        playlist_name: str,
        content_type: str,
        is_spotify: bool
    ) -> None:
        """プレイリスト/アルバムの処理"""
        added_count = 0
        for track in tracks:
            player.queue.put(track)
            added_count += 1

        logger.info(f"プレイリストをキューに追加: {playlist_name} ({added_count}曲)")

        total_duration = sum(t.length for t in tracks)
        source_info = "Spotify → SoundCloud" if is_spotify else "SoundCloud"
        is_album = content_type == "album"
        first_artwork = getattr(tracks[0], 'artwork', None) if tracks else None

        if not player.playing and not player.queue.is_empty:
            try:
                next_track = player.queue.get()
                await player.play(next_track)
                logger.info(f"再生開始: {next_track.title}")

                view = PlaylistAddView(
                    playlist_name=playlist_name,
                    track_count=added_count,
                    total_duration=self._format_duration(total_duration),
                    source=source_info,
                    first_track=next_track.title,
                    is_album=is_album,
                    thumbnail_url=first_artwork,
                    is_playing=True
                )

            except Exception as e:
                logger.error(f"プレイリスト再生開始エラー: {e}")
                view = MusicErrorView(
                    title="再生エラー",
                    description=f"プレイリストの再生を開始できませんでした。\n`{e}`"
                )
        else:
            view = PlaylistAddView(
                playlist_name=playlist_name,
                track_count=added_count,
                total_duration=self._format_duration(total_duration),
                source=source_info,
                queue_count=len(player.queue),
                is_album=is_album,
                thumbnail_url=first_artwork,
                is_playing=False
            )

        await interaction.followup.send(view=view)

    @app_commands.command(name="play", description="曲を再生またはキューに追加します")
    @app_commands.describe(query="曲名、YouTube/Spotify/SoundCloud URL")
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        """曲を再生"""
        player = await self._ensure_voice(interaction)
        if not player:
            return

        await interaction.response.defer()

        is_spotify = bool(SPOTIFY_REGEX.match(query))
        tracks, playlist_name, content_type = await self._search_tracks(query)

        if not tracks:
            if is_spotify:
                view = MusicErrorView(
                    title="再生ソースが見つかりません",
                    description=(
                        "Spotifyで曲は見つかりましたが、再生可能なソース（SoundCloud）で見つかりませんでした。"
                    ),
                    hint="曲名で直接検索すると見つかる場合があります。"
                )
            else:
                view = MusicErrorView(
                    title="見つかりません",
                    description=f"「{query}」に一致する曲が見つかりませんでした。"
                )
            await interaction.followup.send(view=view)
            return

        # プレイリスト/アルバムの場合
        if playlist_name and len(tracks) > 1:
            await self._handle_playlist(interaction, player, tracks, playlist_name, content_type, is_spotify)
            return

        # 単一トラックの場合
        track = tracks[0]
        source_info = self._get_source_info(track, is_spotify)

        player.queue.put(track)
        logger.info(f"トラックをキューに追加: {track.title}")

        if not player.playing:
            try:
                next_track = player.queue.get()
                await player.play(next_track)
                logger.info(f"再生リクエスト: {next_track.title}")
                view = TrackRequestView(
                    title=track.title,
                    duration=self._format_duration(track.length),
                    source=source_info,
                    thumbnail_url=getattr(track, 'artwork', None)
                )
            except Exception as e:
                logger.error(f"再生開始エラー: {e}")
                view = MusicErrorView(
                    title="再生エラー",
                    description=f"トラックの再生を開始できませんでした。\n`{e}`"
                )
                await interaction.followup.send(view=view)
                return
        else:
            view = QueueAddView(
                title=track.title,
                duration=self._format_duration(track.length),
                source=source_info,
                position=len(player.queue),
                thumbnail_url=getattr(track, 'artwork', None)
            )

        await interaction.followup.send(view=view)
