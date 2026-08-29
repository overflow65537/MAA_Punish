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

from action.basics.InterfaceZone.roi_zone_classify import load_combat_pipeline_nodes
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

    _SKIP_ACTION_TYPES = {"ClickKey", "KeyDown", "LongPressKey"}

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

            node_data = self._get_base_node_data(context, node_name)
            if not node_data:
                continue

            node_override = self._build_node_override(node_data, zone_offset)
            if node_override:
                overrides[node_name] = node_override

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

    @classmethod
    def _get_base_node_data(
        cls, context: Context, node_name: str
    ) -> dict[str, Any] | None:
        node = load_combat_pipeline_nodes().get(node_name)
        if isinstance(node, dict):
            return node
        return context.get_node_data(node_name)

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

    @staticmethod
    def _is_numeric_list(values: Any, size: int) -> bool:
        return (
            isinstance(values, list)
            and len(values) == size
            and all(isinstance(v, (int, float)) for v in values)
        )

    @classmethod
    def _is_default_roi(cls, roi: Any) -> bool:
        return cls._is_numeric_list(roi, 4) and all(int(v) == 0 for v in roi)

    @staticmethod
    def _apply_offset(values: list[Any], zone_offset: list[int]) -> list[int]:
        count = min(len(values), len(zone_offset))
        return [int(values[i]) + zone_offset[i] for i in range(count)]

    @classmethod
    def _build_node_override(
        cls,
        node_data: dict[str, Any],
        zone_offset: list[int],
    ) -> dict[str, Any] | None:
        recognition_override = cls._build_recognition_override(node_data, zone_offset)
        if recognition_override is not None:
            return recognition_override

        return cls._build_action_override(node_data, zone_offset)

    @classmethod
    def _build_recognition_override(
        cls,
        node_data: dict[str, Any],
        zone_offset: list[int],
    ) -> dict[str, Any] | None:
        recognition = node_data.get("recognition")
        if not isinstance(recognition, dict):
            return None
        if recognition.get("type", "DirectHit") == "DoNothing":
            return None

        param = recognition.get("param")
        if not isinstance(param, dict):
            return None

        roi = param.get("roi")
        if not cls._is_numeric_list(roi, 4) or cls._is_default_roi(roi):
            return None

        return {"recognition": {"param": {"roi": cls._apply_offset(roi, zone_offset)}}}

    @classmethod
    def _build_action_override(
        cls,
        node_data: dict[str, Any],
        zone_offset: list[int],
    ) -> dict[str, Any] | None:
        action = node_data.get("action")
        if not isinstance(action, dict):
            return None

        action_type = action.get("type")
        if action_type in cls._SKIP_ACTION_TYPES:
            return None

        param = action.get("param")
        if not isinstance(param, dict):
            return None

        override_param: dict[str, Any] = {}
        if action_type in {"Click", "TouchDown", "LongPress"}:
            target = param.get("target")
            if isinstance(target, list) and len(target) in (2, 4):
                override_param["target"] = cls._apply_offset(target, zone_offset)
        elif action_type == "Swipe":
            for key in ("begin", "end"):
                point = param.get(key)
                if isinstance(point, list) and len(point) in (2, 4):
                    override_param[key] = cls._apply_offset(point, zone_offset)

        if override_param:
            return {"action": {"param": override_param}}
        return None


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
