"""
MAA_Punish
检查布局 ROI 偏移缓存是否存在
命中 = 需要采集缓存（本地没有可用数据）
作者:overflow65537
"""

from maa.context import Context
from maa.custom_recognition import CustomRecognition

from action.basics.InterfaceZone.LoadRoiZone import LoadRoiZone
from action.basics.InterfaceZone.roi_zone_controller import (
    cache_is_ready,
    parse_controller,
    parse_param,
)
from logger_component import LoggerComponent


class CheckROIZoneCache(CustomRecognition):
    def __init__(self):
        super().__init__()
        self._logger_component = LoggerComponent(__name__)
        self.logger = self._logger_component.logger
        self._loader = LoadRoiZone()

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult | None:
        controller = parse_controller(parse_param(argv.custom_recognition_param))
        if cache_is_ready(controller):
            self.logger.info("CheckROIZoneCache controller=%s 缓存已就绪, 加载偏移", controller)
            self._loader.apply_offsets(context, controller)
            return None
        self.logger.info("CheckROIZoneCache controller=%s 缓存未就绪, 需要采集", controller)
        return CustomRecognition.AnalyzeResult(
            box=(0, 0, 0, 0),
            detail={"status": "need_cache", "controller": controller},
        )
