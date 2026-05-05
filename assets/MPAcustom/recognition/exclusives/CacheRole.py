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

from MPAcustom.logger_component import LoggerComponent


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

    def _past_weekly_threshold(self, now: datetime.datetime) -> bool:
        start_of_week = now - datetime.timedelta(days=now.weekday())
        threshold = datetime.datetime.combine(
            start_of_week.date(), datetime.time(hour=5)
        )
        return now >= threshold

    def _effective_week_key(self, now: datetime.datetime) -> int:
        if self._past_weekly_threshold(now):
            iso = now.isocalendar()
        else:
            iso = (now - datetime.timedelta(days=7)).isocalendar()
        year, week = int(iso[0]), int(iso[1])
        return year * 100 + week

    def _past_monthly_threshold(self, now: datetime.datetime) -> bool:
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
        logger_component = LoggerComponent(__name__)
        logger = logger_component.logger
        params = self._parse_params(argv.custom_recognition_param)
        update_frequency = self._normalize_frequency(params.get("update_frequency"))
        cache_path = Path(__file__).resolve().parents[3] / "role_cache.json"
        logger.info(f"[CacheRole] 启动检查, update_frequency={update_frequency}, cache_path={cache_path}")
        now = datetime.datetime.now()
        if not cache_path.exists():
            logger.info("[CacheRole] 缓存文件不存在, 返回 success 触发更新")
            try:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                init_data = {"main_update_at": now.timestamp()}
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(init_data, f, ensure_ascii=False, indent=2)
                logger.info(f"[CacheRole] 已初始化缓存文件并记录 main_update_at={now}")
            except OSError as e:
                logger.warning(f"[CacheRole] 初始化缓存文件失败: {e}")
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100), detail={"status": "success"}
            )
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
        except (OSError, json.JSONDecodeError):
            cache_data = None
        if not cache_data:
            logger.info("[CacheRole] 缓存文件为空或解析失败, 返回 success 触发更新")
            try:
                init_data = {"main_update_at": now.timestamp()}
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(init_data, f, ensure_ascii=False, indent=2)
                logger.info(f"[CacheRole] 已重置缓存文件并记录 main_update_at={now}")
            except OSError as e:
                logger.warning(f"[CacheRole] 重置缓存文件失败: {e}")
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100), detail={"status": "success"}
            )

        # 额外的周更键：只更新缓存值（不触发完整更新）
        try:
            week_key_name = "cage_update_week"
            current_week = self._effective_week_key(now)
            stored_week_raw = cache_data.get(week_key_name)
            stored_week = int(stored_week_raw) if isinstance(stored_week_raw, int) else None

            if stored_week != current_week:
                logger.info(
                    f"[CacheRole] cage周更触发: stored_week={stored_week}, current_week={current_week}, "
                    "原因: 当前周key与缓存不同, 重置cage值为3"
                )
                focus = cache_data.get("focus")
                if isinstance(focus, dict):
                    for _, role_info in focus.items():
                        if isinstance(role_info, dict):
                            role_info["cage"] = 3
                cache_data[week_key_name] = current_week
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
            else:
                logger.debug(
                    f"[CacheRole] cage周更跳过: stored_week={stored_week}, current_week={current_week}, "
                    "原因: 已在本周更新过cage值"
                )
        except OSError as e:
            logger.warning(f"[CacheRole] cage周更写入失败: {e}")

        if update_frequency == "never":
            logger.info("[CacheRole] update_frequency=never, 不触发完整更新, 返回 None")
            return None

        # 检查必要键是否缺失
        focus = cache_data.get("focus")
        if not isinstance(focus, dict) or focus is None:
            logger.info("[CacheRole] focus 缺失或无效, 直接触发更新")
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100), detail={"status": "success"}
            )

        # 主更新记录保存到 config（role_cache.json）中：main_update_at
        # - 只使用 main_update_at，不再依赖/回退到文件 mtime
        try:
            main_key_name = "main_update_at"
            stored_main_ts = self._parse_main_update_at(cache_data.get(main_key_name))

            if stored_main_ts is None:
                logger.info("[CacheRole] main_update_at 缺失或无法解析, 直接触发更新")
                cache_data[main_key_name] = now.timestamp()
                try:
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                except OSError as e:
                    logger.warning(f"[CacheRole] 写入main_update_at失败: {e}")
                return CustomRecognition.AnalyzeResult(
                    box=(0, 0, 100, 100), detail={"status": "success"}
                )

            last_update = datetime.datetime.fromtimestamp(stored_main_ts)
            logger.debug(f"[CacheRole] 上次完整更新时间: {last_update} (timestamp={stored_main_ts})")
        except OSError as e:
            logger.warning(f"[CacheRole] 读取main_update_at失败, 回退到epoch: {e}")
            last_update = datetime.datetime.fromtimestamp(0)

        if update_frequency == "monthly":
            same_month = self._same_month(last_update, now)
            past_threshold = self._past_monthly_threshold(now)
            needs_update = (not same_month) and past_threshold
            logger.info(
                f"[CacheRole] 月更检查: last_update={last_update}, same_month={same_month}, "
                f"past_threshold={past_threshold}, needs_update={needs_update}"
            )
            if not needs_update:
                if same_month:
                    logger.info("[CacheRole] 不更新: 已在本月更新过")
                elif not past_threshold:
                    logger.info("[CacheRole] 不更新: 未到达本月阈值(每月1号5:00后才触发)")
        else:
            same_week = self._same_week(last_update, now)
            past_threshold = self._past_weekly_threshold(now)
            needs_update = (not same_week) and past_threshold
            logger.info(
                f"[CacheRole] 周更检查: last_update={last_update}, same_week={same_week}, "
                f"past_threshold={past_threshold}, needs_update={needs_update}"
            )
            if not needs_update:
                if same_week:
                    logger.info("[CacheRole] 不更新: 已在本周更新过")
                elif not past_threshold:
                    logger.info("[CacheRole] 不更新: 未到达本周阈值(本周一5:00后才触发)")

        if needs_update:
            logger.info("[CacheRole] 返回 success 触发完整更新")
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100), detail={"status": "success"}
            )
        logger.info("[CacheRole] 无需更新, 返回 None")
        return None
