"""
時間文字列パーサー
"1d12h30m" のような形式を秒数に変換
"""
from __future__ import annotations

import re
from typing import Optional


# 時間単位と秒数のマッピング
TIME_UNITS = {
    "w": 604800,   # 週
    "d": 86400,    # 日
    "h": 3600,     # 時間
    "m": 60,       # 分
    "s": 1,        # 秒
}

# パターン: 数字 + 単位 の繰り返し
TIME_PATTERN = re.compile(r"(\d+)([wdhms])", re.IGNORECASE)


def parse_duration(duration_str: str) -> Optional[int]:
    """
    時間文字列を秒数に変換

    Args:
        duration_str: "1d12h30m" のような形式

    Returns:
        秒数（パース失敗時はNone）

    Examples:
        parse_duration("1d") -> 86400
        parse_duration("12h") -> 43200
        parse_duration("1d12h30m") -> 131400
        parse_duration("1w") -> 604800
    """
    if not duration_str:
        return None

    duration_str = duration_str.strip().lower()

    # 数字のみの場合は分として扱う
    if duration_str.isdigit():
        return int(duration_str) * 60

    matches = TIME_PATTERN.findall(duration_str)
    if not matches:
        return None

    total_seconds = 0
    for value, unit in matches:
        total_seconds += int(value) * TIME_UNITS.get(unit, 0)

    return total_seconds if total_seconds > 0 else None


def format_duration(seconds: int) -> str:
    """
    秒数を人間が読みやすい形式に変換

    Args:
        seconds: 秒数

    Returns:
        "1日12時間30分" のような形式
    """
    if seconds <= 0:
        return "0秒"

    parts = []

    weeks = seconds // 604800
    seconds %= 604800
    if weeks:
        parts.append(f"{weeks}週間")

    days = seconds // 86400
    seconds %= 86400
    if days:
        parts.append(f"{days}日")

    hours = seconds // 3600
    seconds %= 3600
    if hours:
        parts.append(f"{hours}時間")

    minutes = seconds // 60
    seconds %= 60
    if minutes:
        parts.append(f"{minutes}分")

    if seconds:
        parts.append(f"{seconds}秒")

    return "".join(parts) if parts else "0秒"
