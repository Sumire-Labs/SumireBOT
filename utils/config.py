"""
設定ファイル (config.yaml) の読み込みと管理
"""
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Optional


class Config:
    """config.yaml の設定を管理するクラス"""

    _instance: Optional[Config] = None

    def __new__(cls, config_path: str = "config.yaml") -> Config:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str = "config.yaml") -> None:
        if self._initialized:
            return
        self._config_path = Path(config_path)
        self._config = self._load_config()
        self._initialized = True

    def _load_config(self) -> dict[str, Any]:
        """設定ファイルを読み込む"""
        if not self._config_path.exists():
            raise FileNotFoundError(
                f"設定ファイルが見つかりません: {self._config_path}\n"
                f"config.yaml.example を config.yaml にコピーして設定してください。"
            )

        with open(self._config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def reload(self) -> None:
        """設定ファイルを再読み込み"""
        self._config = self._load_config()

    def get(self, *keys: str, default: Any = None) -> Any:
        """ネストしたキーから値を取得"""
        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default
        return value

    # BOT設定
    @property
    def token(self) -> str:
        """BOTトークン"""
        return self.get("bot", "token", default="")

    @property
    def description(self) -> str:
        """BOT説明文"""
        return self.get("bot", "description", default="すみれBot v2")

    # UI設定
    @property
    def embed_color(self) -> int:
        """メインEmbed色"""
        return self.get("ui", "embed_color", default=0x9B59B6)

    @property
    def success_color(self) -> int:
        """成功時のEmbed色"""
        return self.get("ui", "success_color", default=0x2ECC71)

    @property
    def error_color(self) -> int:
        """エラー時のEmbed色"""
        return self.get("ui", "error_color", default=0xE74C3C)

    @property
    def warning_color(self) -> int:
        """警告時のEmbed色"""
        return self.get("ui", "warning_color", default=0xF39C12)

    @property
    def info_color(self) -> int:
        """情報表示のEmbed色"""
        return self.get("ui", "info_color", default=0x3498DB)

    # データベース設定
    @property
    def database_path(self) -> str:
        """データベースファイルパス"""
        return self.get("database", "path", default="database/sumire.db")

    # ログ設定
    @property
    def log_level(self) -> str:
        """ログレベル"""
        return self.get("logging", "level", default="INFO")

    @property
    def log_file(self) -> str:
        """ログファイルパス"""
        return self.get("logging", "file", default="logs/bot.log")

    @property
    def log_console(self) -> bool:
        """コンソール出力の有無"""
        return self.get("logging", "console", default=True)

    # 翻訳設定
    @property
    def default_target_language(self) -> str:
        """デフォルトの翻訳先言語"""
        return self.get("translate", "default_target_language", default="ja")

    # チケット設定
    @property
    def ticket_channel_prefix(self) -> str:
        """チケットチャンネルのプレフィックス"""
        return self.get("ticket", "channel_prefix", default="ticket")

    @property
    def ticket_categories(self) -> list[str]:
        """チケットカテゴリー一覧"""
        return self.get("ticket", "categories", default=[
            "一般的な質問",
            "技術サポート",
            "バグ報告",
            "機能リクエスト",
            "その他"
        ])

    # 音楽設定
    @property
    def lavalink_uri(self) -> str:
        """Lavalink サーバーURI"""
        return self.get("music", "lavalink", "uri", default="http://localhost:2333")

    @property
    def lavalink_password(self) -> str:
        """Lavalink パスワード"""
        return self.get("music", "lavalink", "password", default="youshallnotpass")

    @property
    def music_default_volume(self) -> int:
        """デフォルト音量"""
        return self.get("music", "default_volume", default=50)

    @property
    def music_auto_leave_timeout(self) -> int:
        """自動退出時間（秒）"""
        return self.get("music", "auto_leave_timeout", default=180)

    @property
    def spotify_client_id(self) -> str:
        """Spotify Client ID"""
        return self.get("music", "spotify", "client_id", default="")

    @property
    def spotify_client_secret(self) -> str:
        """Spotify Client Secret"""
        return self.get("music", "spotify", "client_secret", default="")
