"""
MAA_Punish
MAA_Punish 检查角色缓存
作者:overflow65537
"""

import datetime
from maa.custom_recognition import CustomRecognition
from maa.define import OCRResult
import json
from pathlib import Path


class CacheRole(CustomRecognition):
    def _is_same_week(self, last_week) -> bool:
        try:
            last_week_int = int(last_week)
        except (TypeError, ValueError):
            return False
        current_week = datetime.date.today().isocalendar().week
        return last_week_int == current_week

    def analyze(
        self,
        context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult | None:
        cache_path = Path(__file__).parent / "role_cache.json"
        if not cache_path.exists():
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100), detail={"status": "success"}
            )
        with open(cache_path, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        if not cache_data:
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100), detail={"status": "success"}
            )
        last_time = cache_data.get("last_time")
        needs_update = (not last_time) or (not self._is_same_week(last_time))
        if needs_update:
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100), detail={"status": "success"}
            )
        return None
