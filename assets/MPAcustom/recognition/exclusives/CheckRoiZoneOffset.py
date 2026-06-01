"""
MAA_Punish
MAA_Punish 检查 ROI 区偏移配置是否存在
作者:overflow65537
"""

from maa.context import Context
from maa.custom_recognition import CustomRecognition

from MPAcustom.logger_component import LoggerComponent
from action.basics.InterfaceZone.roi_zone_controller import (
    offset_path,
    parse_controller,
    parse_param,
)


class CheckRoiZoneOffset(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult | None:
        logger = LoggerComponent(__name__).logger
        controller = parse_controller(parse_param(argv.custom_recognition_param))
        offset_path_file = offset_path(controller)

        if offset_path_file.exists():
            logger.info(
                "[CheckRoiZoneOffset] 偏移配置已存在 (%s), 返回 success",
                offset_path_file,
            )
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100),
                detail={
                    "status": "success",
                    "message": f"{offset_path_file} 已存在",
                    "controller": controller,
                },
            )

        logger.info(
            "[CheckRoiZoneOffset] 偏移配置不存在 (%s), 返回 None",
            offset_path_file,
        )
        context.run_task("缓存ROI偏移配置")
        return None
