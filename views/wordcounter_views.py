"""
単語カウンター用 Components V2 View
"""
from __future__ import annotations

from typing import Optional

import discord
from discord import ui

from utils.database import Database
from utils.config import Config
from utils.logging import get_logger

logger = get_logger("sumire.views.wordcounter")


class AddWordModal(ui.Modal, title="単語を追加"):
    """単語追加モーダル"""

    word = ui.TextInput(
        label="カウントする単語",
        placeholder="例: 草",
        max_length=50,
        min_length=1
    )

    def __init__(self, settings_view: "WordCounterSettingsView") -> None:
        super().__init__()
        self.settings_view = settings_view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """モーダル送信時"""
        word = self.word.value.strip()

        if not word:
            await interaction.response.send_message("単語を入力してください。", ephemeral=True)
            return

        if word in self.settings_view.words:
            await interaction.response.send_message(f"「{word}」は既に登録されています。", ephemeral=True)
            return

        # 単語を追加
        db = Database()
        await db.add_counter_word(self.settings_view.guild.id, word)
        self.settings_view.words.append(word)

        # UIを更新
        self.settings_view.clear_items()
        self.settings_view._build_ui()
        await interaction.response.edit_message(view=self.settings_view)

        logger.info(f"単語追加: {word} in {self.settings_view.guild.name}")


class WordCounterSettingsView(ui.LayoutView):
    """単語カウンター設定パネル"""

    def __init__(
        self,
        guild: discord.Guild,
        enabled: bool = True,
        words: list[str] = None
    ) -> None:
        super().__init__(timeout=300)
        self.guild = guild
        self.db = Database()
        self.config = Config()
        self.enabled = enabled
        self.words = words or []

        self._build_ui()

    def _build_ui(self) -> None:
        """UIを構築"""
        container = ui.Container(accent_colour=discord.Colour.blue())

        container.add_item(ui.TextDisplay("# 🔢 単語カウンター設定"))
        container.add_item(ui.Separator())

        # ステータス
        status_emoji = "🟢" if self.enabled else "🔴"
        status_text = "有効" if self.enabled else "無効"
        container.add_item(ui.TextDisplay(f"**ステータス:** {status_emoji} {status_text}"))

        # 登録済み単語
        if self.words:
            words_text = "\n".join([f"• {word}" for word in self.words[:15]])
            if len(self.words) > 15:
                words_text += f"\n... 他 {len(self.words) - 15} 個"
            container.add_item(ui.TextDisplay(f"**登録済み単語:**\n{words_text}"))
        else:
            container.add_item(ui.TextDisplay("**登録済み単語:** なし"))

        container.add_item(ui.Separator())

        # 有効/無効ボタン
        toggle_row = ui.ActionRow()
        if self.enabled:
            toggle_row.add_item(ui.Button(
                label="無効にする",
                style=discord.ButtonStyle.danger,
                custom_id="wordcounter:settings:disable"
            ))
        else:
            toggle_row.add_item(ui.Button(
                label="有効にする",
                style=discord.ButtonStyle.success,
                custom_id="wordcounter:settings:enable"
            ))
        container.add_item(toggle_row)

        # 単語追加ボタン
        add_row = ui.ActionRow()
        add_row.add_item(ui.Button(
            label="単語を追加",
            style=discord.ButtonStyle.primary,
            custom_id="wordcounter:settings:add"
        ))
        container.add_item(add_row)

        # 単語選択（削除用）
        if self.words:
            select_row = ui.ActionRow()
            options = [
                discord.SelectOption(label=word, value=word)
                for word in self.words[:25]
            ]
            select = ui.StringSelect(
                placeholder="削除する単語を選択...",
                options=options,
                custom_id="wordcounter:settings:remove"
            )
            select_row.add_item(select)
            container.add_item(select_row)

            # 全削除ボタン
            clear_row = ui.ActionRow()
            clear_row.add_item(ui.Button(
                label="すべて削除",
                style=discord.ButtonStyle.secondary,
                custom_id="wordcounter:settings:clear"
            ))
            container.add_item(clear_row)

        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """インタラクションのチェックとルーティング"""
        custom_id = interaction.data.get("custom_id", "")

        if custom_id == "wordcounter:settings:enable":
            await self._toggle_enabled(interaction, True)
            return False
        elif custom_id == "wordcounter:settings:disable":
            await self._toggle_enabled(interaction, False)
            return False
        elif custom_id == "wordcounter:settings:add":
            await self._show_add_modal(interaction)
            return False
        elif custom_id == "wordcounter:settings:remove":
            await self._remove_word(interaction)
            return False
        elif custom_id == "wordcounter:settings:clear":
            await self._clear_words(interaction)
            return False

        return True

    async def _toggle_enabled(self, interaction: discord.Interaction, enabled: bool) -> None:
        """有効/無効を切り替え"""
        await interaction.response.defer()
        await self.db.set_wordcounter_enabled(self.guild.id, enabled)
        self.enabled = enabled

        self.clear_items()
        self._build_ui()
        await interaction.edit_original_response(view=self)

        status = "有効" if enabled else "無効"
        logger.info(f"単語カウンター{status}化: {self.guild.name}")

    async def _show_add_modal(self, interaction: discord.Interaction) -> None:
        """単語追加モーダルを表示"""
        modal = AddWordModal(self)
        await interaction.response.send_modal(modal)

    async def _remove_word(self, interaction: discord.Interaction) -> None:
        """単語を削除"""
        await interaction.response.defer()

        selected = interaction.data.get("values", [])
        if not selected:
            return

        word = selected[0]
        await self.db.remove_counter_word(self.guild.id, word)
        if word in self.words:
            self.words.remove(word)

        self.clear_items()
        self._build_ui()
        await interaction.edit_original_response(view=self)

        logger.info(f"単語削除: {word} in {self.guild.name}")

    async def _clear_words(self, interaction: discord.Interaction) -> None:
        """すべての単語を削除"""
        await interaction.response.defer()
        await self.db.clear_counter_words(self.guild.id)
        self.words = []

        self.clear_items()
        self._build_ui()
        await interaction.edit_original_response(view=self)

        logger.info(f"全単語削除: {self.guild.name}")


class WordCounterLeaderboardView(ui.LayoutView):
    """単語カウンターランキング表示View"""

    def __init__(
        self,
        guild: discord.Guild,
        word: Optional[str],
        rankings: list[dict]
    ) -> None:
        super().__init__(timeout=300)

        container = ui.Container(accent_colour=discord.Colour.blue())

        # ヘッダー
        if word:
            container.add_item(ui.TextDisplay(f"# 🏆 単語カウンターランキング - 「{word}」"))
        else:
            container.add_item(ui.TextDisplay("# 🏆 単語カウンター 総合ランキング"))

        container.add_item(ui.Separator())

        # ランキング
        medals = ["🥇", "🥈", "🥉"]
        ranking_text = ""

        for idx, data in enumerate(rankings, 1):
            medal = medals[idx - 1] if idx <= 3 else f"**{idx}.**"
            user_id = data["user_id"]
            count = data.get("count") or data.get("total_count", 0)
            ranking_text += f"{medal} <@{user_id}> - **{count}回**\n"

        if ranking_text:
            container.add_item(ui.TextDisplay(ranking_text))
        else:
            container.add_item(ui.TextDisplay("データがありません"))

        self.add_item(container)


class WordCounterMyCountView(ui.LayoutView):
    """自分の単語カウント表示View"""

    def __init__(
        self,
        user: discord.User,
        counts: list[dict]
    ) -> None:
        super().__init__(timeout=300)

        container = ui.Container(accent_colour=discord.Colour.blue())

        container.add_item(ui.TextDisplay(f"# 📊 {user.display_name} のカウント"))
        container.add_item(ui.Separator())

        # カウント一覧
        count_text = ""
        for data in counts[:20]:
            word = data["word"]
            count = data["count"]
            count_text += f"• **{word}**: {count}回\n"

        if len(counts) > 20:
            count_text += f"\n... 他 {len(counts) - 20} 個"

        if count_text:
            container.add_item(ui.TextDisplay(count_text))
        else:
            container.add_item(ui.TextDisplay("データがありません"))

        self.add_item(container)
