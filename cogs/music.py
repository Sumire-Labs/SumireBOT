"""
音楽プレイヤー Cog
Wavelink + Lavalink を使用した音楽再生機能
"""
from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING, Optional, Union, cast

import discord
import wavelink
from discord import app_commands
from discord.ext import commands

from utils.config import Config
from utils.database import Database
from utils.embeds import EmbedBuilder
from utils.logging import get_logger
from utils.checks import handle_app_command_error
from views.music_views import (
    NowPlayingView,
    TrackRequestView,
    QueueAddView,
    PlaylistAddView,
    MusicErrorView,
    MusicWarningView,
    MusicSuccessView,
    MusicInfoView,
)

if TYPE_CHECKING:
    from bot import SumireBot

logger = get_logger("sumire.cogs.music")

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


class Music(commands.Cog):
    """音楽プレイヤー"""

    def __init__(self, bot: SumireBot) -> None:
        self.bot = bot
        self.config = Config()
        self.db = Database()
        self.embed_builder = EmbedBuilder()
        # サーバーごとのループ設定
        self.loop_mode: dict[int, str] = {}  # guild_id -> "off" | "track" | "queue"
        # 自動退出タイマー
        self._auto_leave_tasks: dict[int, asyncio.Task] = {}

    async def cog_load(self) -> None:
        """Cog読み込み時にLavalinkに接続"""
        node = wavelink.Node(
            uri=self.config.lavalink_uri,
            password=self.config.lavalink_password,
        )
        await wavelink.Pool.connect(nodes=[node], client=self.bot, cache_capacity=100)
        logger.info(f"Lavalink に接続しました: {self.config.lavalink_uri}")

    async def cog_unload(self) -> None:
        """Cog アンロード時にクリーンアップ"""
        # 全ての自動退出タスクをキャンセル
        for task in self._auto_leave_tasks.values():
            task.cancel()
        self._auto_leave_tasks.clear()

    # ==================== イベントリスナー ====================

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        """Wavelink ノード準備完了"""
        logger.info(f"Wavelink ノード準備完了: {payload.node.identifier}")

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ) -> None:
        """ボイスステート更新時（Bot切断検知）"""
        # Bot自身の状態変更のみ処理
        if member.id != self.bot.user.id:
            return

        # VCから切断された場合（before.channel あり → after.channel なし）
        if before.channel is not None and after.channel is None:
            guild_id = member.guild.id
            logger.info(f"VC切断を検知: guild_id={guild_id}")

            # ループモードをリセット
            if guild_id in self.loop_mode:
                del self.loop_mode[guild_id]

            # 自動退出タイマーをキャンセル
            if guild_id in self._auto_leave_tasks:
                self._auto_leave_tasks[guild_id].cancel()
                del self._auto_leave_tasks[guild_id]

            # キューのクリア（プレイヤーがまだ存在する場合）
            player = cast(wavelink.Player, member.guild.voice_client)
            if player:
                player.queue.clear()
                logger.info(f"キューをクリア: guild_id={guild_id}")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        """トラック再生開始"""
        player = payload.player
        if not player:
            return

        guild_id = player.guild.id

        # 自動退出タイマーをキャンセル
        if guild_id in self._auto_leave_tasks:
            self._auto_leave_tasks[guild_id].cancel()
            del self._auto_leave_tasks[guild_id]

        # Now Playing メッセージを送信
        track = payload.track
        playback_source = self._get_playback_source(track)
        loop = self.loop_mode.get(guild_id, "off")

        view = NowPlayingView(
            title=track.title,
            author=track.author,
            duration=self._format_duration(track.length),
            source=playback_source,
            queue_count=len(player.queue) if player.queue else 0,
            loop_mode=loop if loop != "off" else None,
            thumbnail_url=getattr(track, 'artwork', None)
        )

        # チャンネルに送信
        if player.channel:
            try:
                await player.channel.send(view=view)
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        """トラック再生終了"""
        player = payload.player
        if not player:
            return

        guild_id = player.guild.id
        loop = self.loop_mode.get(guild_id, "off")

        # ループモードの処理
        if loop == "track" and payload.track:
            # 同じトラックを再度再生
            await player.play(payload.track)
            return
        elif loop == "queue" and payload.track:
            # キューの末尾に追加
            player.queue.put(payload.track)

        # キューに曲があれば次を再生
        if not player.queue.is_empty:
            try:
                next_track = player.queue.get()
                await player.play(next_track)
            except Exception as e:
                logger.error(f"次のトラック再生エラー: {e}")
            return

        # キューが空になったら自動退出タイマーを開始
        if not player.playing:
            self._start_auto_leave_timer(guild_id, player)

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player) -> None:
        """プレイヤーが非アクティブになった時"""
        if not player.guild:
            return
        guild_id = player.guild.id
        logger.debug(f"プレイヤーが非アクティブ: guild_id={guild_id}")
        self._start_auto_leave_timer(guild_id, player)

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload) -> None:
        """トラック再生エラー"""
        player = payload.player
        if not player or not player.guild:
            return

        track = payload.track
        exception_msg = str(payload.exception) if payload.exception else "不明なエラー"
        logger.error(f"トラック再生エラー: {track.title if track else 'Unknown'} - {exception_msg}")

        # エラーメッセージをチャンネルに送信
        if player.channel:
            try:
                track_name = track.title if track else "曲"

                # エラーの種類に応じたメッセージ
                if "No playable" in exception_msg or "not found" in exception_msg.lower():
                    view = MusicErrorView(
                        title="再生ソースが見つかりません",
                        description=(
                            f"**{track_name}** の再生ソースが見つかりませんでした。\n\n"
                            "Spotifyのメタデータは取得できましたが、"
                            "SoundCloudに同じ曲が存在しないか、利用できません。"
                        ),
                        hint="曲名やアーティスト名で直接検索してみてください。"
                    )
                elif "age restricted" in exception_msg.lower():
                    view = MusicErrorView(
                        title="年齢制限",
                        description=f"**{track_name}** は年齢制限があるため再生できません。"
                    )
                elif "region" in exception_msg.lower() or "country" in exception_msg.lower():
                    view = MusicErrorView(
                        title="地域制限",
                        description=f"**{track_name}** はこの地域では利用できません。"
                    )
                else:
                    view = MusicErrorView(
                        title="再生エラー",
                        description=f"**{track_name}** の再生中にエラーが発生しました。\n\n`{exception_msg[:150]}`"
                    )

                await player.channel.send(view=view)

                # 次の曲があることを通知
                if not player.queue.is_empty:
                    info_view = MusicInfoView(
                        title="自動スキップ",
                        description="次の曲を自動的に再生します..."
                    )
                    await player.channel.send(view=info_view)
            except discord.Forbidden:
                pass

        # 次の曲があれば再生を試みる
        if not player.queue.is_empty:
            try:
                next_track = player.queue.get()
                await player.play(next_track)
            except Exception as e:
                logger.error(f"次のトラック再生エラー: {e}")

    @commands.Cog.listener()
    async def on_wavelink_track_stuck(self, payload: wavelink.TrackStuckEventPayload) -> None:
        """トラックがスタックした時"""
        player = payload.player
        if not player or not player.guild:
            return

        track = payload.track
        logger.warning(f"トラックがスタック: {track.title if track else 'Unknown'} - threshold={payload.threshold}ms")

        # ユーザーに通知
        if player.channel:
            try:
                track_name = track.title if track else "曲"
                footer = "次の曲を自動的に再生します..." if not player.queue.is_empty else None

                view = MusicWarningView(
                    title="再生が停止しました",
                    description=(
                        f"**{track_name}** の再生が停止しました。\n"
                        "ストリーミングソースからの応答がありません。"
                    ),
                    footer=footer
                )
                await player.channel.send(view=view)
            except discord.Forbidden:
                pass

        # スキップして次の曲へ
        if not player.queue.is_empty:
            try:
                next_track = player.queue.get()
                await player.play(next_track)
            except Exception as e:
                logger.error(f"スタック後の再生エラー: {e}")

    # ==================== ヘルパーメソッド ====================

    def _start_auto_leave_timer(self, guild_id: int, player: wavelink.Player) -> None:
        """自動退出タイマーを開始"""
        # 既存のタイマーをキャンセル
        if guild_id in self._auto_leave_tasks:
            self._auto_leave_tasks[guild_id].cancel()

        async def auto_leave():
            try:
                await asyncio.sleep(self.config.music_auto_leave_timeout)
                if player.connected and not player.playing:
                    await player.disconnect()
                    logger.info(f"自動退出: guild_id={guild_id}")

                    # 退出メッセージ
                    if player.channel:
                        try:
                            view = MusicInfoView(
                                title="自動退出",
                                description="3分間何も再生されなかったため、ボイスチャンネルから退出しました。"
                            )
                            await player.channel.send(view=view)
                        except discord.Forbidden:
                            pass
            except asyncio.CancelledError:
                pass
            finally:
                if guild_id in self._auto_leave_tasks:
                    del self._auto_leave_tasks[guild_id]

        self._auto_leave_tasks[guild_id] = asyncio.create_task(auto_leave())

    def _format_duration(self, milliseconds: int) -> str:
        """ミリ秒を mm:ss 形式に変換"""
        seconds = milliseconds // 1000
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    def _get_source_info(self, track: wavelink.Playable, is_spotify_request: bool = False) -> str:
        """トラックのソース情報を取得"""
        uri = track.uri or ""

        # Spotifyリクエストの場合
        if is_spotify_request:
            if "soundcloud" in uri.lower():
                return "Spotify → SoundCloud"
            elif "youtube" in uri.lower():
                return "Spotify → YouTube"
            else:
                return "Spotify経由"

        # URI から判定
        if "soundcloud" in uri.lower():
            return "SoundCloud"
        elif "music.youtube" in uri.lower():
            return "YouTube Music"
        elif "youtube" in uri.lower():
            return "YouTube"
        else:
            return "検索結果"

    def _get_playback_source(self, track: wavelink.Playable) -> str:
        """実際の再生ソースを取得（Now Playing用）"""
        uri = track.uri or ""
        if "soundcloud" in uri.lower():
            return "SoundCloud"
        elif "music.youtube" in uri.lower():
            return "YouTube Music"
        elif "youtube" in uri.lower():
            return "YouTube"
        else:
            return "ストリーム"

    async def _get_player(self, interaction: discord.Interaction) -> Optional[wavelink.Player]:
        """現在のプレイヤーを取得（エラーチェック付き）"""
        if not interaction.guild:
            return None

        player = cast(wavelink.Player, interaction.guild.voice_client)
        return player

    async def _ensure_voice(self, interaction: discord.Interaction) -> Optional[wavelink.Player]:
        """ボイスチャンネルに接続を確保"""
        if not interaction.guild:
            embed = self.embed_builder.error(
                title="エラー",
                description="このコマンドはサーバー内でのみ使用できます。"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return None

        # ユーザーがボイスチャンネルにいるかチェック
        if not interaction.user.voice or not interaction.user.voice.channel:
            embed = self.embed_builder.error(
                title="エラー",
                description="先にボイスチャンネルに参加してください。"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return None

        player = cast(wavelink.Player, interaction.guild.voice_client)

        # まだ接続していない場合は接続
        if not player:
            try:
                player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
                player.autoplay = wavelink.AutoPlayMode.disabled
                # デフォルト音量を設定
                await player.set_volume(self.config.music_default_volume)
                logger.info(f"ボイスチャンネルに接続: {interaction.user.voice.channel.name}")
            except discord.ClientException as e:
                embed = self.embed_builder.error(
                    title="接続エラー",
                    description=f"ボイスチャンネルに接続できませんでした。\n{e}"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return None
        else:
            # 違うチャンネルにいる場合
            if player.channel != interaction.user.voice.channel:
                embed = self.embed_builder.error(
                    title="エラー",
                    description="Botと同じボイスチャンネルに参加してください。"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return None

        return player

    async def _search_tracks(self, query: str) -> tuple[list[wavelink.Playable], Optional[str], Optional[str]]:
        """
        曲を検索

        Returns:
            tuple: (トラックリスト, プレイリスト名またはNone, タイプ "track"|"playlist"|"album"|None)
        """
        # Spotify URL の処理
        spotify_match = SPOTIFY_REGEX.match(query)
        if spotify_match:
            spotify_type = spotify_match.group(1)  # track, album, playlist
            try:
                logger.info(f"Spotify {spotify_type} 検索: {query}")
                result = await wavelink.Playable.search(query)

                # プレイリスト/アルバムの場合
                if isinstance(result, wavelink.Playlist):
                    tracks = list(result.tracks)
                    playlist_name = result.name or f"Spotify {spotify_type}"
                    logger.info(f"プレイリスト取得: {playlist_name} ({len(tracks)}曲)")
                    return (tracks, playlist_name, spotify_type)

                # 単一トラックの場合
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

                # プレイリストの場合
                if isinstance(result, wavelink.Playlist):
                    tracks = list(result.tracks)
                    playlist_name = result.name or "YouTube Playlist"
                    logger.info(f"YouTubeプレイリスト取得: {playlist_name} ({len(tracks)}曲)")
                    return (tracks, playlist_name, "playlist")

                # 単一トラックの場合
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

        # テキスト検索（検索ソースのリスト、優先順）
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

        # 最終フォールバック: SoundCloud（プレフィックス直接指定）
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

    # ==================== コマンド ====================

    @app_commands.command(name="play", description="曲を再生またはキューに追加します")
    @app_commands.describe(query="曲名、YouTube/Spotify/SoundCloud URL")
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        """曲を再生"""
        player = await self._ensure_voice(interaction)
        if not player:
            return

        await interaction.response.defer()

        # Spotify URL かどうかを判定
        is_spotify = bool(SPOTIFY_REGEX.match(query))

        # 曲を検索
        tracks, playlist_name, content_type = await self._search_tracks(query)

        if not tracks:
            # Spotify URL の場合、SoundCloudで見つからなかった可能性を示唆
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

        # キューに追加
        player.queue.put(track)
        logger.info(f"トラックをキューに追加: {track.title}")

        # 再生中でなければ再生開始
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
        # 全曲をキューに追加
        added_count = 0
        for track in tracks:
            player.queue.put(track)
            added_count += 1

        logger.info(f"プレイリストをキューに追加: {playlist_name} ({added_count}曲)")

        # 総再生時間を計算
        total_duration = sum(t.length for t in tracks)
        source_info = "Spotify → SoundCloud" if is_spotify else "SoundCloud"
        is_album = content_type == "album"
        first_artwork = getattr(tracks[0], 'artwork', None) if tracks else None

        # 再生中でなければ再生開始
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
            # 既に再生中の場合
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

    @app_commands.command(name="skip", description="現在の曲をスキップします")
    async def skip(self, interaction: discord.Interaction) -> None:
        """曲をスキップ"""
        player = await self._get_player(interaction)

        if not player or not player.playing:
            view = MusicErrorView(
                title="エラー",
                description="現在再生中の曲がありません。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # ユーザーが同じチャンネルにいるかチェック
        if not interaction.user.voice or player.channel != interaction.user.voice.channel:
            view = MusicErrorView(
                title="エラー",
                description="Botと同じボイスチャンネルに参加してください。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        current_track = player.current
        await player.skip()

        view = MusicSuccessView(
            title="スキップ",
            description=f"**{current_track.title}** をスキップしました。"
        )
        await interaction.response.send_message(view=view)

    @app_commands.command(name="leave", description="再生を停止してボイスチャンネルから退出します")
    async def leave(self, interaction: discord.Interaction) -> None:
        """再生停止 & 退出"""
        player = await self._get_player(interaction)

        if not player:
            view = MusicErrorView(
                title="エラー",
                description="現在ボイスチャンネルに接続していません。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # ユーザーが同じチャンネルにいるかチェック
        if not interaction.user.voice or player.channel != interaction.user.voice.channel:
            view = MusicErrorView(
                title="エラー",
                description="Botと同じボイスチャンネルに参加してください。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # キューをクリアして停止
        player.queue.clear()
        await player.stop()

        # ループモードをリセット
        guild_id = interaction.guild.id
        if guild_id in self.loop_mode:
            del self.loop_mode[guild_id]

        # 自動退出タイマーをキャンセル
        if guild_id in self._auto_leave_tasks:
            self._auto_leave_tasks[guild_id].cancel()
            del self._auto_leave_tasks[guild_id]

        # VCから切断
        await player.disconnect()

        view = MusicSuccessView(
            title="退出",
            description="再生を停止し、ボイスチャンネルから退出しました。"
        )
        await interaction.response.send_message(view=view)

    @app_commands.command(name="loop", description="ループモードを切り替えます")
    @app_commands.describe(mode="ループモード")
    @app_commands.choices(mode=[
        app_commands.Choice(name="オフ", value="off"),
        app_commands.Choice(name="トラック", value="track"),
        app_commands.Choice(name="キュー", value="queue"),
    ])
    async def loop(self, interaction: discord.Interaction, mode: str) -> None:
        """ループモードを設定"""
        player = await self._get_player(interaction)

        if not player:
            view = MusicErrorView(
                title="エラー",
                description="現在再生中ではありません。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # ユーザーが同じチャンネルにいるかチェック
        if not interaction.user.voice or player.channel != interaction.user.voice.channel:
            view = MusicErrorView(
                title="エラー",
                description="Botと同じボイスチャンネルに参加してください。"
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        guild_id = interaction.guild.id
        self.loop_mode[guild_id] = mode

        mode_text = {
            "off": "オフ",
            "track": "🔂 トラック（1曲リピート）",
            "queue": "🔁 キュー（全曲リピート）"
        }

        view = MusicSuccessView(
            title="ループ設定",
            description=f"ループモードを **{mode_text[mode]}** に設定しました。"
        )
        await interaction.response.send_message(view=view)

    # ==================== エラーハンドリング ====================

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ) -> None:
        """コマンドエラーハンドリング"""
        await handle_app_command_error(interaction, error, "Music")


async def setup(bot: commands.Bot) -> None:
    """Cogのセットアップ"""
    await bot.add_cog(Music(bot))
