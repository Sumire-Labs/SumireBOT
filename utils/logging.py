"""
ロギングシステムの設定
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """ロギングを設定"""
    logger = logging.getLogger("sumire")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # フォーマッター
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # コンソールハンドラー
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # ファイルハンドラー
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(
            log_path,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # discord.pyのログを設定
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(logging.WARNING)

    return logger


def get_logger(name: str = "sumire") -> logging.Logger:
    """ロガーを取得"""
    return logging.getLogger(name)
