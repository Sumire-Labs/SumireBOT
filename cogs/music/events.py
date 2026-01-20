"""
Music イベントリスナー
"""
from __future__ import annotations

import asyncio
from typing import cast

import discord
import wavelink
from discord.ext import commands

from utils.logging import get_logger
from views.music_views import (
    NowPlayingView,
    MusicErrorView,
    MusicWarningView,
    MusicInfoView,
)

logger = get_logger("sumire.cogs.music.events")


class EventsMixin:
    """Music イベントリスナー Mixin"""

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
        if member.id != self.bot.user.id:
            return

        if before.channel is not None and after.channel is None:
            guild_id = member.guild.id
            logger.info(f"VC切断を検知: guild_id={guild_id}")

            if guild_id in self.loop_mode:
                del self.loop_mode[guild_id]

            if guild_id in self._auto_leave_tasks:
                self._auto_leave_tasks[guild_id].cancel()
                del self._auto_leave_tasks[guild_id]

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

        if player.autoplay != wavelink.AutoPlayMode.disabled:
            player.autoplay = wavelink.AutoPlayMode.disabled
            logger.debug("autoplayを無効化しました")

        guild_id = player.guild.id

        if guild_id in self._auto_leave_tasks:
            self._auto_leave_tasks[guild_id].cancel()
            del self._auto_leave_tasks[guild_id]

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

        reason = str(payload.reason) if payload.reason else "unknown"
        logger.debug(f"トラック終了: reason={reason}, track={payload.track.title if payload.track else 'None'}")

        if payload.reason and "finished" not in reason.lower():
            logger.debug(f"正常終了ではないためスキップ: reason={reason}")
            return

        guild_id = player.guild.id
        loop = self.loop_mode.get(guild_id, "off")

        if loop == "track" and payload.track:
            await player.play(payload.track)
            return
        elif loop == "queue" and payload.track:
            player.queue.put(payload.track)

        if not player.queue.is_empty:
            try:
                next_track = player.queue.get()
                await player.play(next_track)
            except Exception as e:
                logger.error(f"次のトラック再生エラー: {e}")
            return

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

        if player.channel:
            try:
                track_name = track.title if track else "曲"

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

                if not player.queue.is_empty:
                    info_view = MusicInfoView(
                        title="自動スキップ",
                        description="次の曲を自動的に再生します..."
                    )
                    await player.channel.send(view=info_view)
            except discord.Forbidden:
                pass

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

        if not player.queue.is_empty:
            try:
                next_track = player.queue.get()
                await player.play(next_track)
            except Exception as e:
                logger.error(f"スタック後の再生エラー: {e}")
