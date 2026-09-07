"""
MAA_Punish
MAA_Punish 载入识别区
作者:overflow65537
"""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any

from maa.context import Context
from maa.custom_action import CustomAction
from logger_component import LoggerComponent

from action.basics.InterfaceZone.roi_zone_controller import (
    offset_path,
    parse_controller,
    parse_param,
)
from action.basics.InterfaceZone.ReadRoiZone import capture_roi_zones

_ZONE_MAP_PATH = Path(__file__).with_name("combat_roi_zone_map.json")


class LoadRoiZone(CustomAction):
    _OFFSET_EXCLUDED_NODES = frozenset({"战斗中"})

    _ZONE_OFFSET_KEYS: dict[str, str] = {
        "ATK_ROI_ZONE": "atk_zone",
        "DODGE_ROI_ZONE": "dodge_zone",
        "SKILL_ROI_ZONE": "skill_zone",
        "LENS_LOCK_ROI_ZONE": "lock_zone",
        "AUXILIARY_MACHINE_ROI_ZONE": "assist_zone",
        "SINGNAL_BALL_ROI_ZONE": "signal_zone",
        "SWITCH_ROI_ZONE": "switch_zone",
        "CORE_ROI_ZONE": "corepass_zone",
    }

    def __init__(self):
        super().__init__()
        self._logger_component = LoggerComponent(__name__)
        self.logger = self._logger_component.logger

    def __getattr__(self, name: str) -> list[str]:
        if name in self._ZONE_OFFSET_KEYS:
            return _get_zone_lists()[name]
        raise AttributeError(name)

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        params = parse_param(argv.custom_action_param)
        controller = parse_controller(params)

        if params.get("from_screen"):
            self.logger.info(
                "LoadRoiZone controller=%s 在布局界面读取识别区",
                controller,
            )
            capture_roi_zones(context, controller)

        self.apply_offsets(context, controller)
        return CustomAction.RunResult(success=True)

    def apply_offsets(self, context: Context, controller: str) -> None:
        offset_file = offset_path(controller)
        if not offset_file.exists():
            self.logger.warning(
                "LoadRoiZone controller=%s 偏移配置不存在 (%s), 跳过加载",
                controller,
                offset_file,
            )
            return

        self.logger.info(
            "LoadRoiZone controller=%s 读取偏移配置 (%s)",
            controller,
            offset_file,
        )

        with open(offset_file, "r", encoding="utf-8") as f:
            offset_data = json.load(f)

        node_zone_map = _get_node_zone_map()
        overrides: dict[str, Any] = {}
        for node_name, offset_key in node_zone_map.items():
            if node_name in self._OFFSET_EXCLUDED_NODES:
                continue

            zone_offset = self._get_zone_offset(offset_data, offset_key)
            if zone_offset is None:
                continue

            overrides[node_name] = {
                "recognition": {
                    "param": {
                        "roi_offset": zone_offset,
                    }
                }
            }

        if overrides:
            context.override_pipeline(overrides)
            self.logger.info(
                "LoadRoiZone controller=%s 本次覆盖 %d 个节点 (%s):\n%s",
                controller,
                len(overrides),
                offset_file,
                json.dumps(overrides, ensure_ascii=False, indent=2),
            )
        else:
            self.logger.info("LoadRoiZone 本次无覆盖内容")

    @staticmethod
    def _get_zone_offset(offset_data: dict, offset_key: str) -> list[int] | None:
        zone = offset_data.get(offset_key)
        if not isinstance(zone, dict):
            return None
        if not zone.get("hit"):
            return None
        offset = zone.get("offset")
        if (
            not isinstance(offset, list)
            or len(offset) != 4
            or not all(isinstance(v, (int, float)) for v in offset)
        ):
            return None
        return [int(v) for v in offset]


@lru_cache(maxsize=1)
def _load_zone_map_file() -> dict[str, Any]:
    if not _ZONE_MAP_PATH.is_file():
        raise FileNotFoundError(
            f"缺少 {_ZONE_MAP_PATH.name}，请运行 tools/gen_combat_roi_zone_map.py 生成"
        )
    with open(_ZONE_MAP_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{_ZONE_MAP_PATH.name} 格式无效")
    return data


@lru_cache(maxsize=1)
def _get_node_zone_map() -> dict[str, str]:
    raw = _load_zone_map_file().get("node_zone_map", {})
    if not isinstance(raw, dict):
        raise ValueError(f"{_ZONE_MAP_PATH.name} 缺少 node_zone_map")
    return {str(name): str(zone_key) for name, zone_key in raw.items()}


@lru_cache(maxsize=1)
def _get_zone_lists() -> dict[str, list[str]]:
    attr_by_key = {
        offset_key: attr for attr, offset_key in LoadRoiZone._ZONE_OFFSET_KEYS.items()
    }
    lists: dict[str, list[str]] = {
        attr: [] for attr in LoadRoiZone._ZONE_OFFSET_KEYS
    }
    for node_name, offset_key in sorted(_get_node_zone_map().items()):
        attr = attr_by_key.get(offset_key)
        if attr is not None:
            lists[attr].append(node_name)
    return lists
