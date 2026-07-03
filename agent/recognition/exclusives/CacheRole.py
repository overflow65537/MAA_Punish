"""
MAA_Punish
MAA_Punish 检查角色缓存
作者:overflow65537
"""

import datetime
from maa.custom_recognition import CustomRecognition
from typing import Any

from action.basics import role_cache_policy as cache_policy
from logger_component import LoggerComponent


class CacheRole(CustomRecognition):
    def _parse_params(self, raw_params: Any) -> dict[str, Any]:
        if isinstance(raw_params, dict):
            return raw_params
        if isinstance(raw_params, str):
            import json

            try:
                parsed = json.loads(raw_params)
            except json.JSONDecodeError:
                return {}
            if isinstance(parsed, dict):
                return parsed
        return {}

    def analyze(
        self,
        context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult | None:
        logger_component = LoggerComponent(__name__)
        logger = logger_component.logger
        params = self._parse_params(argv.custom_recognition_param)
        update_frequency = cache_policy.normalize_frequency(
            params.get("update_frequency")
        )
        cache_prefix = cache_policy.resolve_cache_prefix(param=params)
        cache_prefix_source = cache_policy.resolve_cache_prefix_source(param=params)
        cache_path = cache_policy.cache_path(cache_prefix)
        logger.info(
            f"[CacheRole] 启动检查, update_frequency={update_frequency}, "
            f"cache_prefix={cache_prefix!r}, cache_path={cache_path}"
        )
        now = datetime.datetime.now()
        if not cache_path.exists():
            logger.info(
                "[CacheRole] 缓存文件不存在, cache_path=%s, cache_file=%s, "
                "cache_prefix=%r, cache_prefix_source=%s, update_frequency=%s, "
                "返回 success 触发更新",
                cache_path,
                cache_path.name,
                cache_prefix,
                cache_prefix_source,
                update_frequency,
            )
            try:
                init_data = {
                    "main_update_at": now.timestamp(),
                    "update_frequency": update_frequency,
                }
                cache_policy.write_cache_data(init_data, cache_path)
                logger.info(
                    f"[CacheRole] 已初始化缓存文件并记录 main_update_at={now}"
                )
            except OSError as e:
                logger.warning(f"[CacheRole] 初始化缓存文件失败: {e}")
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100), detail={"status": "success"}
            )

        cache_data = cache_policy.read_cache_data(cache_path)
        if not cache_data:
            logger.info("[CacheRole] 缓存文件为空或解析失败, 返回 success 触发更新")
            try:
                init_data = {
                    "main_update_at": now.timestamp(),
                    "update_frequency": update_frequency,
                }
                cache_policy.write_cache_data(init_data, cache_path)
                logger.info(f"[CacheRole] 已重置缓存文件并记录 main_update_at={now}")
            except OSError as e:
                logger.warning(f"[CacheRole] 重置缓存文件失败: {e}")
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100), detail={"status": "success"}
            )

        cache_data["update_frequency"] = update_frequency

        try:
            if cache_policy.apply_cage_weekly_reset(cache_data, now):
                logger.info(
                    "[CacheRole] cage周更触发: 当前周 key 与缓存不同, 重置 cage 值为 3"
                )
                cache_policy.write_cache_data(cache_data, cache_path)
            else:
                logger.debug("[CacheRole] cage周更跳过: 已在本周更新过 cage 值")
        except OSError as e:
            logger.warning(f"[CacheRole] cage周更写入失败: {e}")

        if update_frequency == "never":
            try:
                cache_policy.write_cache_data(cache_data, cache_path)
            except OSError as e:
                logger.warning(f"[CacheRole] 写入 update_frequency 失败: {e}")
            logger.info("[CacheRole] update_frequency=never, 不触发完整更新, 返回 None")
            return None

        focus = cache_policy.get_focus(cache_data)
        if focus is None:
            logger.info("[CacheRole] focus 缺失或无效, 直接触发更新")
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100), detail={"status": "success"}
            )

        main_key_name = "main_update_at"
        stored_main_ts = cache_policy.parse_main_update_at(
            cache_data.get(main_key_name)
        )
        if stored_main_ts is None:
            logger.info("[CacheRole] main_update_at 缺失或无法解析, 直接触发更新")
            cache_data[main_key_name] = now.timestamp()
            try:
                cache_policy.write_cache_data(cache_data, cache_path)
            except OSError as e:
                logger.warning(f"[CacheRole] 写入main_update_at失败: {e}")
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100), detail={"status": "success"}
            )

        last_update = datetime.datetime.fromtimestamp(stored_main_ts)
        logger.debug(
            f"[CacheRole] 上次完整更新时间: {last_update} (timestamp={stored_main_ts})"
        )

        if cache_policy.needs_full_refresh(cache_data, update_frequency):
            if update_frequency == "monthly":
                same_month = cache_policy.same_month(last_update, now)
                past_threshold = cache_policy.past_monthly_threshold(now)
                logger.info(
                    f"[CacheRole] 月更检查: last_update={last_update}, same_month={same_month}, "
                    f"past_threshold={past_threshold}, needs_update=True"
                )
            else:
                same_week = cache_policy.same_week(last_update, now)
                past_threshold = cache_policy.past_weekly_threshold(now)
                logger.info(
                    f"[CacheRole] 周更检查: last_update={last_update}, same_week={same_week}, "
                    f"past_threshold={past_threshold}, needs_update=True"
                )
            logger.info("[CacheRole] 返回 success 触发完整更新")
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100), detail={"status": "success"}
            )

        try:
            cache_policy.write_cache_data(cache_data, cache_path)
        except OSError as e:
            logger.warning(f"[CacheRole] 写入 update_frequency 失败: {e}")

        if update_frequency == "monthly":
            logger.info("[CacheRole] 不更新: 已在本月更新过")
        else:
            logger.info("[CacheRole] 不更新: 已在本周更新过")
        logger.info("[CacheRole] 无需更新, 返回 None")
        return None
