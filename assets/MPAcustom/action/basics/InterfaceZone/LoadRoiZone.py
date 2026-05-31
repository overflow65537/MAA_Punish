"""
MAA_Punish
MAA_Punish 载入识别区
作者:overflow65537
"""

from pathlib import Path
from typing import Any

from maa.context import Context
from maa.custom_action import CustomAction
from MPAcustom.logger_component import LoggerComponent
import json


class LoadRoiZone(CustomAction):
    ATK_ROI_ZONE = [
        "攻击",
        "长按攻击",
        "按下攻击",
        "检查角色",
        "检查普攻1_霁梦",
        "检查普攻2_霁梦",
        "检查比安卡·深痕一阶段",
        "检查阶段p1_深谣",
        "检查阶段p2_深谣",
    ]
    DODGE_ROI_ZONE = [
        "闪避",
        "长按闪避",
        "按下闪避",
        "检查闪避",
        "战斗中",
        "检查希声长闪",
        "检查核心被动_深痕",
        "检查核心被动_晖暮",
    ]
    SKILL_ROI_ZONE = [
        "技能",
        "长按技能",
        "检查u1_誓焰",
        "检查u2_誓焰",
        "检查u3_誓焰",
    ]
    LENS_LOCK_ROI_ZONE = ["锁定视角"]
    AUXILIARY_MACHINE_ROI_ZONE = ["辅助机"]
    SINGNAL_BALL_ROI_ZONE = [
        "消球1",
        "消球2",
        "消球3",
        "消球4",
        "消球5",
        "消球6",
        "消球7",
        "消球8",
        "长按1号球",
        "识别信号球",
        "_信号球数量",
        "检查希声红球",
        "检查核心球_霁梦",
        "检查核心被动1_深谣",
        "检查核心被动2_深谣",
    ]
    SWITCH_ROI_ZONE = [
        "qte1",
        "qte2",
        "检查蓝色QTE待激发",
        "检查红色QTE待激发",
        "检查黄色QTE待激发",
        "切换黄色QTE",
        "切换红色QTE",
        "切换蓝色QTE",
    ]
    CORE_ROI_ZONE = [
        "检查极锋核心条1",
        "检查希声2阶段",
        "检查骇影2阶段",
        "检查核心条2_霁梦",
        "检查核心条_霁梦",
        "检查核心条_铮骨",
        "检查残月值_终焉",
        "检查无光值_囚影",
        "检查u3_max",
        "检查p1动能条_誓焰",
        "检查p2动能条_深谣",
        "检查核心技能_超刻",
        "检查核心技能结束_超刻",
    ]

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
    _POINT_ACTION_TYPES = {"Click", "TouchDown"}

    def __init__(self):
        self._logger_component = LoggerComponent(__name__)
        self.logger = self._logger_component.logger

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        with open(Path("roi_zone_offset.json"), "r", encoding="utf-8") as f:
            offset_data = json.load(f)

        overrides: dict[str, Any] = {}
        for zone_attr, offset_key in self._ZONE_OFFSET_KEYS.items():
            zone_offset = self._get_zone_offset(offset_data, offset_key)
            if zone_offset is None:
                continue

            for node_name in getattr(self, zone_attr):
                node_data = context.get_node_data(node_name)
                if not node_data:
                    continue

                node_override = self._build_node_override(
                    node_name, node_data, zone_offset
                )
                if node_override:
                    overrides.update(node_override)

        if overrides:
            context.override_pipeline(overrides)
            self.logger.info(
                "LoadRoiZone 本次覆盖 %d 个节点:\n%s",
                len(overrides),
                json.dumps(overrides, ensure_ascii=False, indent=2),
            )
        else:
            self.logger.info("LoadRoiZone 本次无覆盖内容")

        return CustomAction.RunResult(success=True)

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
    def _is_numeric_roi(roi: Any) -> bool:
        return (
            isinstance(roi, list)
            and len(roi) == 4
            and all(isinstance(v, (int, float)) for v in roi)
        )

    @staticmethod
    def _is_point(value: Any) -> bool:
        return (
            isinstance(value, list)
            and len(value) >= 2
            and all(isinstance(v, (int, float)) for v in value[:2])
        )

    @classmethod
    def _build_node_override(
        cls,
        node_name: str,
        node_data: dict[str, Any],
        zone_offset: list[int],
    ) -> dict[str, Any] | None:
        recognition_override = cls._build_recognition_override(node_data, zone_offset)
        if recognition_override is not None:
            return {node_name: recognition_override}

        action_override = cls._build_action_override(node_data, zone_offset)
        if action_override is not None:
            return {node_name: action_override}

        return None

    @classmethod
    def _build_recognition_override(
        cls,
        node_data: dict[str, Any],
        zone_offset: list[int],
    ) -> dict[str, Any] | None:
        recognition = node_data.get("recognition")
        if not isinstance(recognition, dict):
            return None

        param = recognition.get("param")
        if not isinstance(param, dict):
            return None

        roi = param.get("roi")
        if not cls._is_numeric_roi(roi):
            return None

        roi_offset = param.get("roi_offset")
        if roi_offset is None:
            return {"recognition": {"param": {"roi_offset": zone_offset}}}

        new_roi = [int(roi[i]) + zone_offset[i] for i in range(4)]
        return {"recognition": {"param": {"roi": new_roi}}}

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
            param = {}

        if action_type in cls._POINT_ACTION_TYPES:
            return cls._build_point_override(
                param, "target", "target_offset", zone_offset
            )

        if action_type == "Swipe":
            override_param: dict[str, Any] = {}
            for point_key, offset_key in (
                ("begin", "begin_offset"),
                ("end", "end_offset"),
            ):
                point_override = cls._build_point_param_override(
                    param, point_key, offset_key, zone_offset
                )
                if point_override:
                    override_param.update(point_override)
            if override_param:
                return {"action": {"param": override_param}}
            return None

        return None

    @classmethod
    def _build_point_override(
        cls,
        param: dict[str, Any],
        point_key: str,
        offset_key: str,
        zone_offset: list[int],
    ) -> dict[str, Any] | None:
        point_override = cls._build_point_param_override(
            param, point_key, offset_key, zone_offset
        )
        if point_override:
            return {"action": {"param": point_override}}
        return None

    @classmethod
    def _build_point_param_override(
        cls,
        param: dict[str, Any],
        point_key: str,
        offset_key: str,
        zone_offset: list[int],
    ) -> dict[str, Any] | None:
        point = param.get(point_key)
        if not cls._is_point(point):
            return None

        point_offset = param.get(offset_key)
        if point_offset is None:
            return {offset_key: zone_offset}

        new_point = list(point)
        new_point[0] = int(new_point[0]) + zone_offset[0]
        new_point[1] = int(new_point[1]) + zone_offset[1]
        return {point_key: new_point}
