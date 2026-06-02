"""
MAA_Punish
MAA_Punish 检查 ROI 区偏移配置是否存在
作者:overflow65537
"""

from maa.context import Context
from maa.custom_recognition import CustomRecognition

from MPAcustom.logger_component import LoggerComponent
from action.basics.InterfaceZone.roi_zone_controller import (
    is_adaptive_layout_enabled,
    offset_path,
    parse_controller,
    parse_param,
)

_READ_ROI_NODE = "识别区域"
_LOAD_ROI_NODE = "覆盖布局菜单"


def _controller_param(controller: str) -> dict[str, str]:
    return {"controller": controller}


def _read_roi_override(controller: str) -> dict:
    return {
        _READ_ROI_NODE: {
            "action": {
                "type": "Custom",
                "param": {
                    "custom_action": "ReadROIZone",
                    "custom_action_param": _controller_param(controller),
                },
            },
        },
    }


def _load_roi_override(controller: str) -> dict:
    return {
        _LOAD_ROI_NODE: {
            "action": {
                "type": "Custom",
                "param": {
                    "custom_action": "LoadROIZone",
                    "custom_action_param": _controller_param(controller),
                },
            },
        },
    }


class CheckRoiZoneOffset(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult | None:
        logger = LoggerComponent(__name__).logger
        controller = parse_controller(parse_param(argv.custom_recognition_param))

        if not is_adaptive_layout_enabled(context):
            logger.info(
                "[CheckRoiZoneOffset] controller=%s 自适应布局已关闭, 跳过 ROI 偏移流程",
                controller,
            )
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100),
                detail={
                    "status": "skipped",
                    "message": "自适应布局已关闭",
                    "controller": controller,
                },
            )

        offset_file = offset_path(controller)

        if offset_file.exists():
            context.override_pipeline(_load_roi_override(controller))
            logger.info(
                "[CheckRoiZoneOffset] controller=%s 偏移配置已存在 (%s), 返回 success",
                controller,
                offset_file,
            )
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100),
                detail={
                    "status": "success",
                    "message": f"{offset_file} 已存在",
                    "controller": controller,
                },
            )

        logger.info(
            "[CheckRoiZoneOffset] controller=%s 偏移配置不存在 (%s), 触发缓存",
            controller,
            offset_file,
        )
        context.run_task(
            "缓存ROI偏移配置",
            pipeline_override=_read_roi_override(controller),
        )
        return None
