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

    def _effective_week_key(self, now: datetime.datetime) -> int:
        if self._past_weekly_threshold():
            iso = now.isocalendar()
        else:
            iso = (now - datetime.timedelta(days=7)).isocalendar()
        year, week = int(iso[0]), int(iso[1])
        return year * 100 + week

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

    def _parse_main_update_at(self, raw: Any) -> float | None:
        if isinstance(raw, (int, float)):
            return float(raw)
        if isinstance(raw, str):
            s = raw.strip()
            if s.isdigit():
                return float(s)
            try:
                dt = datetime.datetime.fromisoformat(s)
                return dt.timestamp()
            except ValueError:
                return None
        return None

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

        now = datetime.datetime.now()
        # 额外的周更键：只更新缓存值（不触发完整更新）
        try:
            week_key_name = "cage_update_week"
            current_week = self._effective_week_key(now)
            stored_week_raw = cache_data.get(week_key_name)
            stored_week = int(stored_week_raw) if isinstance(stored_week_raw, int) else None

            if stored_week != current_week:
                focus = cache_data.get("focus")
                if isinstance(focus, dict):
                    for _, role_info in focus.items():
                        if isinstance(role_info, dict):
                            role_info["cage"] = 3
                cache_data[week_key_name] = current_week
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

        if update_frequency == "never":
            return None

        # 主更新记录保存到 config（role_cache.json）中：main_update_at
        # - 只使用 main_update_at，不再依赖/回退到文件 mtime
        try:
            main_key_name = "main_update_at"
            stored_main_ts = self._parse_main_update_at(cache_data.get(main_key_name))

            if stored_main_ts is None:
                stored_main_ts = 0.0
                cache_data[main_key_name] = stored_main_ts
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)

            last_update = datetime.datetime.fromtimestamp(stored_main_ts)
        except OSError:
            last_update = datetime.datetime.fromtimestamp(0)

        if update_frequency == "monthly":
            needs_update = (not self._same_month(last_update, now)) and self._past_monthly_threshold()
        else:
            needs_update = (not self._same_week(last_update, now)) and self._past_weekly_threshold()
        if needs_update:
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100), detail={"status": "success"}
            )
        return None
