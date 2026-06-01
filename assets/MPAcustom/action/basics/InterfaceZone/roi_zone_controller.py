"""
MAA_Punish
ROI 区偏移：控制器类型、默认 zones 与 debug 校准文件路径
"""

from pathlib import Path
import json
from typing import Any

# 魔法变量：两套默认 zones（adb 为模拟器布局，win32 为 PC 客户端实测 recognized）
_ADB_ZONES: tuple[tuple[str, str, list[int]], ...] = (
    ("atk_zone", "识别攻击区", [1132, 572, 124, 123]),
    ("dodge_zone", "识别闪避区", [992, 571, 124, 124]),
    ("skill_zone", "识别大招区", [853, 571, 124, 126]),
    ("signal_zone", "识别信号球区", [414, 439, 853, 116]),
    ("corepass_zone", "识别核心被动区", [493, 602, 294, 50]),
    ("assist_zone", "识别辅助机区", [1168, 340, 92, 93]),
    ("lock_zone", "识别锁定区", [1070, 344, 81, 82]),
    ("switch_zone", "识别换人区", [1160, 110, 107, 231]),
)

_WIN32_ZONES: tuple[tuple[str, str, list[int]], ...] = (
    ("atk_zone", "识别攻击区", [1144, 583, 101, 101]),
    ("dodge_zone", "识别闪避区", [1006, 584, 99, 99]),
    ("skill_zone", "识别大招区", [865, 584, 100, 99]),
    ("signal_zone", "识别信号球区", [567, 451, 681, 91]),
    ("corepass_zone", "识别核心被动区", [523, 607, 234, 38]),
    ("assist_zone", "识别辅助机区", [1176, 349, 76, 76]),
    ("lock_zone", "识别锁定区", [1064, 352, 64, 64]),
    ("switch_zone", "识别换人区", [1171, 136, 84, 184]),
)

ZONES_BY_CONTROLLER: dict[str, tuple[tuple[str, str, list[int]], ...]] = {
    "adb": _ADB_ZONES,
    "win32": _WIN32_ZONES,
}

OFFSET_FILES: dict[str, Path] = {
    "adb": Path("debug") / "adb_zone_offset.json",
    "win32": Path("debug") / "win32_zone_offset.json",
}


def parse_controller(param: object) -> str:
    if not param:
        return "adb"
    if isinstance(param, str):
        if param in OFFSET_FILES:
            return param
        try:
            param = json.loads(param)
        except json.JSONDecodeError:
            return param.lower() if param.lower() in OFFSET_FILES else "adb"
    if isinstance(param, dict):
        for key in ("controller", "platform", "mode", "type"):
            value = param.get(key)
            if isinstance(value, str) and value in OFFSET_FILES:
                return value
    return "adb"


def offset_path(controller: str) -> Path:
    return OFFSET_FILES.get(controller, OFFSET_FILES["adb"])


def zones_for(controller: str) -> tuple[tuple[str, str, list[int]], ...]:
    return ZONES_BY_CONTROLLER.get(controller, ZONES_BY_CONTROLLER["adb"])


def parse_param(raw_param: Any) -> dict[str, Any]:
    if isinstance(raw_param, dict):
        return raw_param
    if isinstance(raw_param, str):
        try:
            parsed = json.loads(raw_param)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}
