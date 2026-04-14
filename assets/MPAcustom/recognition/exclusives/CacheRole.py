"""
MAA_Punish
MAA_Punish 检查角色缓存
作者:overflow65537
"""

import datetime
from maa.custom_recognition import CustomRecognition
import json
from pathlib import Path
from typing import Any


class CacheRole(CustomRecognition):
    def _parse_params(self, raw_params: Any) -> dict[str, Any]:
        if isinstance(raw_params, dict):
            return raw_params
        if isinstance(raw_params, str):
            try:
                parsed = json.loads(raw_params)
            except json.JSONDecodeError:
                return {}
            if isinstance(parsed, dict):
                return parsed
        return {}

    def _normalize_frequency(self, value: Any) -> str:
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

    def _past_weekly_threshold(self) -> bool:
        now = datetime.datetime.now()
        start_of_week = now - datetime.timedelta(days=now.weekday())
        threshold = datetime.datetime.combine(
            start_of_week.date(), datetime.time(hour=5)
        )
        return now >= threshold

    def _past_monthly_threshold(self) -> bool:
        now = datetime.datetime.now()
        threshold = datetime.datetime.combine(
            datetime.date(now.year, now.month, 1), datetime.time(hour=5)
        )
        return now >= threshold

    def _same_week(self, last_update: datetime.datetime, now: datetime.datetime) -> bool:
        return last_update.isocalendar()[:2] == now.isocalendar()[:2]

    def _same_month(self, last_update: datetime.datetime, now: datetime.datetime) -> bool:
        return last_update.year == now.year and last_update.month == now.month

    def analyze(
        self,
        context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult | None:
        params = self._parse_params(argv.custom_recognition_param)
        update_frequency = self._normalize_frequency(params.get("update_frequency"))
        cache_path = Path(__file__).resolve().parents[3] / "role_cache.json"
        if not cache_path.exists():
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100), detail={"status": "success"}
            )
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
        except (OSError, json.JSONDecodeError):
            cache_data = None
        if not cache_data:
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100), detail={"status": "success"}
            )
        if update_frequency == "never":
            return None

        now = datetime.datetime.now()
        last_update = datetime.datetime.fromtimestamp(cache_path.stat().st_mtime)
        if update_frequency == "monthly":
            needs_update = (not self._same_month(last_update, now)) and self._past_monthly_threshold()
        else:
            needs_update = (not self._same_week(last_update, now)) and self._past_weekly_threshold()
        if needs_update:
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100), detail={"status": "success"}
            )
        return None
