"""
MAA_Punish
MAA_Punish 检查 ROI 区偏移配置是否存在
作者:overflow65537
"""

from pathlib import Path

from maa.context import Context
from maa.custom_recognition import CustomRecognition

from MPAcustom.logger_component import LoggerComponent

DEFAULT_OFFSET_PATH = Path("roi_zone_offset.json")


class CheckRoiZoneOffset(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult | None:
        logger = LoggerComponent(__name__).logger
        offset_path = DEFAULT_OFFSET_PATH

        if offset_path.exists():
            logger.info("[CheckRoiZoneOffset] 偏移配置已存在, 返回 success")
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100),
                detail={"status": "success", "message": "roi_zone_offset.json 已存在"},
            )

        logger.info("[CheckRoiZoneOffset] 偏移配置不存在, 返回 None")
        context.run_task("缓存ROI偏移配置")
        return None
