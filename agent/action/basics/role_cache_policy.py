"""
角色缓存更新策略（CacheRole / RoleSelection 共用）
"""

from __future__ import annotations

import datetime
import json
import re
from pathlib import Path
from typing import Any

# 与 interface.json 账号前缀 verify 保持一致：仅保留安全文件名字符。
_ALLOWED_PREFIX_CHARS = re.compile(r"[^A-Za-z0-9_\u4e00-\u9fff\-]+")
_MAX_PREFIX_LEN = 32

# 游戏日切（周/月刷新）参考时刻，0-23 整点，按运行机器的本地时间。
# 国服日切为 5 点；国际服各服务器时区不同，玩家可自行换算并覆盖。
DEFAULT_REFRESH_HOUR = 5
_REFRESH_HOUR_PATTERN = re.compile(r"\d{1,2}")


def normalize_cache_prefix(value: Any) -> str:
    """过滤路径非法与易混淆符号，仅保留字母/数字/中文/_/-。"""
    if not isinstance(value, str):
        return ""
    prefix = _ALLOWED_PREFIX_CHARS.sub("", value.strip())
    return prefix[:_MAX_PREFIX_LEN]


def cache_path(prefix: str | None = None) -> Path:
    base_dir = Path(__file__).resolve().parents[3]
    norm = normalize_cache_prefix(prefix) if prefix is not None else ""
    if norm:
        return base_dir / f"{norm}_role_cache.json"
    return base_dir / "role_cache.json"


def resolve_cache_prefix(
    attach: dict | None = None,
    param: dict | None = None,
    cache_data: dict | None = None,
) -> str:
    attach = attach or {}
    param = param or {}
    if "cache_prefix" in attach:
        return normalize_cache_prefix(attach["cache_prefix"])
    if "cache_prefix" in param:
        return normalize_cache_prefix(param["cache_prefix"])
    if cache_data and "cache_prefix" in cache_data:
        return normalize_cache_prefix(cache_data["cache_prefix"])
    return ""


def resolve_cache_prefix_source(
    attach: dict | None = None,
    param: dict | None = None,
    cache_data: dict | None = None,
) -> str:
    attach = attach or {}
    param = param or {}
    if "cache_prefix" in attach:
        return "attach.cache_prefix"
    if "cache_prefix" in param:
        return "param.cache_prefix"
    if cache_data and "cache_prefix" in cache_data:
        return "cache_data.cache_prefix"
    return "default"


def normalize_frequency(value: Any) -> str:
    if isinstance(value, str):
        key = value.strip().lower()
    else:
        key = ""
    alias = {
        "weekly": "weekly",
        "week": "weekly",
        "每周": "weekly",
        "每星期": "weekly",
        "monthly": "monthly",
        "month": "monthly",
        "每月": "monthly",
        "never": "never",
        "none": "never",
        "off": "never",
        "不更新": "never",
    }
    return alias.get(key, "weekly")


def normalize_refresh_hour(value: Any) -> int:
    """把刷新时刻规整为 0-23 的整点；非法值回退到 DEFAULT_REFRESH_HOUR。"""
    if isinstance(value, bool):
        return DEFAULT_REFRESH_HOUR
    if isinstance(value, int):
        hour = value
    elif isinstance(value, float):
        if not value.is_integer():
            return DEFAULT_REFRESH_HOUR
        hour = int(value)
    elif isinstance(value, str) and _REFRESH_HOUR_PATTERN.fullmatch(value.strip()):
        hour = int(value.strip())
    else:
        return DEFAULT_REFRESH_HOUR
    if 0 <= hour <= 23:
        return hour
    return DEFAULT_REFRESH_HOUR


def resolve_refresh_hour(
    attach: dict | None = None,
    param: dict | None = None,
    cache_data: dict | None = None,
) -> int:
    """解析刷新时刻，优先级 attach > param > cache_data > 默认(5 点)。"""
    attach = attach or {}
    param = param or {}
    if "refresh_hour" in attach:
        return normalize_refresh_hour(attach["refresh_hour"])
    if "refresh_hour" in param:
        return normalize_refresh_hour(param["refresh_hour"])
    if cache_data and "refresh_hour" in cache_data:
        return normalize_refresh_hour(cache_data["refresh_hour"])
    return DEFAULT_REFRESH_HOUR


def resolve_refresh_hour_source(
    attach: dict | None = None,
    param: dict | None = None,
    cache_data: dict | None = None,
) -> str:
    attach = attach or {}
    param = param or {}
    if "refresh_hour" in attach:
        return "attach.refresh_hour"
    if "refresh_hour" in param:
        return "param.refresh_hour"
    if cache_data and "refresh_hour" in cache_data:
        return "cache_data.refresh_hour"
    return "default"


def read_cache_data(cache_file: Path | None = None) -> dict | None:
    path = cache_file or cache_path()
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    return cache_data if isinstance(cache_data, dict) else None


def write_cache_data(cache_data: dict, cache_file: Path | None = None) -> None:
    path = cache_file or cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)


def parse_main_update_at(raw: Any) -> float | None:
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        s = raw.strip()
        if s.isdigit():
            return float(s)
        try:
            dt = datetime.datetime.fromisoformat(s)
            return dt.timestamp()
        except ValueError:
            return None
    return None


def get_last_update_datetime(cache_data: dict) -> datetime.datetime | None:
    stored_main_ts = parse_main_update_at(cache_data.get("main_update_at"))
    if stored_main_ts is not None:
        return datetime.datetime.fromtimestamp(stored_main_ts)

    last_time = cache_data.get("last_time")
    if isinstance(last_time, int):
        try:
            today = datetime.date.today()
            return datetime.datetime.fromisocalendar(today.year, last_time, 1)
        except ValueError:
            return None
    return None


def past_weekly_threshold(
    now: datetime.datetime, refresh_hour: int = DEFAULT_REFRESH_HOUR
) -> bool:
    """本周刷新时刻（周一 refresh_hour 点）是否已过。"""
    start_of_week = now - datetime.timedelta(days=now.weekday())
    threshold = datetime.datetime.combine(
        start_of_week.date(), datetime.time(hour=normalize_refresh_hour(refresh_hour))
    )
    return now >= threshold


def past_monthly_threshold(
    now: datetime.datetime, refresh_hour: int = DEFAULT_REFRESH_HOUR
) -> bool:
    """本月刷新时刻（1 号 refresh_hour 点）是否已过。"""
    threshold = datetime.datetime.combine(
        datetime.date(now.year, now.month, 1),
        datetime.time(hour=normalize_refresh_hour(refresh_hour)),
    )
    return now >= threshold


def same_week(last_update: datetime.datetime, now: datetime.datetime) -> bool:
    return last_update.isocalendar()[:2] == now.isocalendar()[:2]


def same_month(last_update: datetime.datetime, now: datetime.datetime) -> bool:
    return last_update.year == now.year and last_update.month == now.month


def effective_week_key(
    now: datetime.datetime, refresh_hour: int = DEFAULT_REFRESH_HOUR
) -> int:
    """游戏周键：未过本周刷新时刻时仍算作上一周。"""
    if past_weekly_threshold(now, refresh_hour):
        iso = now.isocalendar()
    else:
        iso = (now - datetime.timedelta(days=7)).isocalendar()
    year, week = int(iso[0]), int(iso[1])
    return year * 100 + week


def resolve_update_frequency(
    attach: dict | None = None,
    param: dict | None = None,
    cache_data: dict | None = None,
) -> str:
    attach = attach or {}
    param = param or {}
    if "update_frequency" in attach:
        return normalize_frequency(attach["update_frequency"])
    if "update_frequency" in param:
        return normalize_frequency(param["update_frequency"])
    if cache_data and "update_frequency" in cache_data:
        return normalize_frequency(cache_data["update_frequency"])
    return "weekly"


def get_focus(cache_data: dict | None) -> dict | None:
    if not cache_data:
        return None
    focus = cache_data.get("focus")
    if not isinstance(focus, dict) or not focus:
        return None
    return focus


def is_focus_usable(
    cache_data: dict | None,
    update_frequency: str,
    now: datetime.datetime | None = None,
) -> bool:
    """配队时是否可直接使用 focus 缓存（跳过滑动识别）。"""
    focus = get_focus(cache_data)
    if focus is None:
        return False

    freq = normalize_frequency(update_frequency)
    if freq == "never":
        return True

    last_update = get_last_update_datetime(cache_data)  # type: ignore[arg-type]
    if last_update is None:
        return False

    now = now or datetime.datetime.now()
    if freq == "monthly":
        return same_month(last_update, now)
    return same_week(last_update, now)


def needs_full_refresh(
    cache_data: dict | None,
    update_frequency: str,
    refresh_hour: int = DEFAULT_REFRESH_HOUR,
    now: datetime.datetime | None = None,
) -> bool:
    """是否应触发完整角色缓存更新（CacheRole）。"""
    freq = normalize_frequency(update_frequency)
    if freq == "never":
        return False

    if get_focus(cache_data) is None:
        return True

    last_update = get_last_update_datetime(cache_data)  # type: ignore[arg-type]
    if last_update is None:
        return True

    now = now or datetime.datetime.now()
    if freq == "monthly":
        return (not same_month(last_update, now)) and past_monthly_threshold(
            now, refresh_hour
        )
    return (not same_week(last_update, now)) and past_weekly_threshold(
        now, refresh_hour
    )


def apply_cage_weekly_reset(
    cache_data: dict,
    now: datetime.datetime | None = None,
    refresh_hour: int = DEFAULT_REFRESH_HOUR,
) -> bool:
    """新周重置 focus 内 cage；有写入返回 True。"""
    now = now or datetime.datetime.now()
    week_key_name = "cage_update_week"
    current_week = effective_week_key(now, refresh_hour)
    stored_week_raw = cache_data.get(week_key_name)
    stored_week = int(stored_week_raw) if isinstance(stored_week_raw, int) else None

    if stored_week == current_week:
        return False

    focus = cache_data.get("focus")
    if isinstance(focus, dict):
        for role_info in focus.values():
            if isinstance(role_info, dict):
                role_info["cage"] = 3
    cache_data[week_key_name] = current_week
    return True
