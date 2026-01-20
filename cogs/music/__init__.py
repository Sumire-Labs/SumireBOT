"""
Music Cog - 音楽プレイヤー
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional, cast

import discord
import wavelink
from discord import app_commands
from discord.ext import commands

from utils.config import Config
from utils.database import Database
from utils.embeds import EmbedBuilder
from utils.logging import get_logger
from utils.checks import handle_app_command_error
from views.music_views import MusicInfoView

from .play import PlayMixin
from .skip import SkipMixin
from .leave import LeaveMixin
from .loop import LoopMixin
from .events import EventsMixin

if TYPE_CHECKING:
    from bot import SumireBot

logger = get_logger("sumire.cogs.music")


class Music(PlayMixin, SkipMixin, LeaveMixin, LoopMixin, EventsMixin, commands.Cog):
    """音楽プレイヤー"""

    def __init__(self, bot: SumireBot) -> None:
        self.bot = bot
        self.config = Config()
        self.db = Database()
        self.embed_builder = EmbedBuilder()
        self.loop_mode: dict[int, str] = {}
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
        for task in self._auto_leave_tasks.values():
            task.cancel()
        self._auto_leave_tasks.clear()

    # ==================== ヘルパーメソッド ====================

    def _start_auto_leave_timer(self, guild_id: int, player: wavelink.Player) -> None:
        """自動退出タイマーを開始"""
        if guild_id in self._auto_leave_tasks:
            self._auto_leave_tasks[guild_id].cancel()

        async def auto_leave():
            try:
                await asyncio.sleep(self.config.music_auto_leave_timeout)
                if player.connected and not player.playing:
                    await player.disconnect()
                    logger.info(f"自動退出: guild_id={guild_id}")

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

        if is_spotify_request:
            if "soundcloud" in uri.lower():
                return "Spotify → SoundCloud"
            elif "youtube" in uri.lower():
                return "Spotify → YouTube"
            else:
                return "Spotify経由"

        if "soundcloud" in uri.lower():
            return "SoundCloud"
        elif "music.youtube" in uri.lower():
            return "YouTube Music"
        elif "youtube" in uri.lower():
            return "YouTube"
        else:
            return "検索結果"

    def _get_playback_source(self, track: wavelink.Playable) -> str:
        """実際の再生ソースを取得"""
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
        """現在のプレイヤーを取得"""
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

        if not interaction.user.voice or not interaction.user.voice.channel:
            embed = self.embed_builder.error(
                title="エラー",
                description="先にボイスチャンネルに参加してください。"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return None

        player = cast(wavelink.Player, interaction.guild.voice_client)

        if not player:
            try:
                player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
                player.autoplay = wavelink.AutoPlayMode.disabled
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
            if player.channel != interaction.user.voice.channel:
                embed = self.embed_builder.error(
                    title="エラー",
                    description="Botと同じボイスチャンネルに参加してください。"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return None

        return player

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
