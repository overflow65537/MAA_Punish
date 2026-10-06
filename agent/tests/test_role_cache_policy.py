"""Tests for role_cache_policy refresh-hour handling (CacheRole / RoleSelection)."""

from __future__ import annotations

import datetime

import pytest

from action.basics import role_cache_policy as policy


def _at(year: int, month: int, day: int, hour: int = 0, minute: int = 0):
    return datetime.datetime(year, month, day, hour, minute)


def _cache_data(last_update: datetime.datetime, *, cage: int = 1) -> dict:
    return {
        "main_update_at": last_update.timestamp(),
        "focus": {"角色A": {"cage": cage}},
    }


class TestNormalizeRefreshHour:
    def test_accepts_valid_hours(self):
        assert policy.normalize_refresh_hour(0) == 0
        assert policy.normalize_refresh_hour(5) == 5
        assert policy.normalize_refresh_hour("23") == 23
        assert policy.normalize_refresh_hour(5.0) == 5
        assert policy.normalize_refresh_hour(" 07 ") == 7

    @pytest.mark.parametrize(
        "value",
        [None, "", "abc", "24", "-1", "5.5", 24, -3, 5.5, True, False, [], {}],
    )
    def test_falls_back_to_default(self, value):
        assert policy.normalize_refresh_hour(value) == policy.DEFAULT_REFRESH_HOUR

    def test_default_is_five(self):
        assert policy.DEFAULT_REFRESH_HOUR == 5


class TestResolveRefreshHour:
    def test_attach_wins(self):
        hour = policy.resolve_refresh_hour(
            {"refresh_hour": 2}, {"refresh_hour": 9}, {"refresh_hour": 11}
        )
        assert hour == 2

    def test_param_wins_over_cache(self):
        hour = policy.resolve_refresh_hour(
            {}, {"refresh_hour": "9"}, {"refresh_hour": 11}
        )
        assert hour == 9

    def test_cache_used_when_no_override(self):
        assert policy.resolve_refresh_hour(None, None, {"refresh_hour": 11}) == 11

    def test_default_when_nothing_given(self):
        assert policy.resolve_refresh_hour() == policy.DEFAULT_REFRESH_HOUR
        assert policy.resolve_refresh_hour({}, {}, {}) == policy.DEFAULT_REFRESH_HOUR

    def test_invalid_attach_value_falls_back_to_default(self):
        hour = policy.resolve_refresh_hour({"refresh_hour": "24"})
        assert hour == policy.DEFAULT_REFRESH_HOUR

    def test_source_reported(self):
        source = policy.resolve_refresh_hour_source
        assert source({"refresh_hour": 2}) == "attach.refresh_hour"
        assert source({}, {"refresh_hour": 2}) == "param.refresh_hour"
        assert source({}, {}, {"refresh_hour": 2}) == "cache_data.refresh_hour"
        assert source() == "default"


class TestResolveUpdateFrequency:
    def test_attach_wins(self):
        freq = policy.resolve_update_frequency(
            {"update_frequency": "monthly"}, {"update_frequency": "never"}
        )
        assert freq == "monthly"

    def test_param_used_without_attach(self):
        assert policy.resolve_update_frequency({}, {"update_frequency": "never"}) == (
            "never"
        )

    def test_default_is_weekly(self):
        assert policy.resolve_update_frequency() == "weekly"


class TestThresholds:
    def test_weekly_threshold_uses_configured_hour(self):
        assert policy.past_weekly_threshold(_at(2026, 10, 5, 4, 59), 5) is False
        assert policy.past_weekly_threshold(_at(2026, 10, 5, 5, 0), 5) is True
        assert policy.past_weekly_threshold(_at(2026, 10, 5, 6, 0), 14) is False
        assert policy.past_weekly_threshold(_at(2026, 10, 5, 14, 0), 14) is True

    def test_reference_date_is_monday(self):
        assert _at(2026, 10, 5).weekday() == 0

    def test_monthly_threshold_uses_configured_hour(self):
        assert policy.past_monthly_threshold(_at(2026, 4, 1, 4, 59), 5) is False
        assert policy.past_monthly_threshold(_at(2026, 4, 1, 5, 0), 5) is True
        assert policy.past_monthly_threshold(_at(2026, 4, 1, 3, 0), 2) is True
        assert policy.past_monthly_threshold(_at(2026, 4, 2, 1, 0), 2) is True

    def test_effective_week_key_switches_at_configured_hour(self):
        before = policy.effective_week_key(_at(2026, 10, 5, 4, 0), 5)
        after = policy.effective_week_key(_at(2026, 10, 5, 6, 0), 5)
        assert before != after
        # 未过刷新时刻时仍算作上一周
        assert before == policy.effective_week_key(_at(2026, 10, 4, 12, 0), 5)


class TestRefreshDecision:
    def test_weekly_before_configured_hour_keeps_cache(self):
        cache = _cache_data(_at(2026, 9, 30, 12, 0))
        now = _at(2026, 10, 5, 4, 0)
        assert policy.needs_full_refresh(cache, "weekly", 5, now) is False

    def test_weekly_after_configured_hour_refreshes(self):
        cache = _cache_data(_at(2026, 9, 30, 12, 0))
        now = _at(2026, 10, 5, 6, 0)
        assert policy.needs_full_refresh(cache, "weekly", 5, now) is True

    def test_earlier_hour_refreshes_earlier(self):
        cache = _cache_data(_at(2026, 9, 30, 12, 0))
        now = _at(2026, 10, 5, 4, 0)
        assert policy.needs_full_refresh(cache, "weekly", 5, now) is False
        assert policy.needs_full_refresh(cache, "weekly", 2, now) is True

    def test_weekly_same_week_never_refreshes(self):
        cache = _cache_data(_at(2026, 10, 7, 3, 0))
        now = _at(2026, 10, 8, 23, 0)
        assert policy.needs_full_refresh(cache, "weekly", 5, now) is False

    def test_monthly_boundary_follows_hour(self):
        cache = _cache_data(_at(2026, 3, 20, 12, 0))
        apr1_before = _at(2026, 4, 1, 3, 0)
        apr1_after = _at(2026, 4, 1, 6, 0)
        assert policy.needs_full_refresh(cache, "monthly", 5, apr1_before) is False
        assert policy.needs_full_refresh(cache, "monthly", 5, apr1_after) is True
        assert policy.needs_full_refresh(cache, "monthly", 2, apr1_before) is True

    def test_never_frequency_short_circuits(self):
        cache = _cache_data(_at(2020, 1, 1, 0, 0))
        now = _at(2026, 10, 5, 12, 0)
        assert policy.needs_full_refresh(cache, "never", 5, now) is False

    def test_missing_focus_needs_refresh(self):
        now = _at(2026, 10, 5, 12, 0)
        assert policy.needs_full_refresh({}, "weekly", 5, now) is True

    def test_missing_last_update_needs_refresh(self):
        cache = {"focus": {"角色A": {"cage": 1}}}
        now = _at(2026, 10, 5, 12, 0)
        assert policy.needs_full_refresh(cache, "weekly", 5, now) is True

    def test_default_arguments_keep_five_am_behaviour(self):
        cache = _cache_data(_at(2026, 9, 30, 12, 0))
        assert policy.needs_full_refresh(cache, "weekly", now=_at(2026, 10, 5, 4)) is False
        assert policy.needs_full_refresh(cache, "weekly", now=_at(2026, 10, 5, 6)) is True


class TestFocusUsable:
    """配队读缓存仍按自然周/月判断，与刷新时刻无关（与改动前一致）。"""

    def test_previous_week_is_not_usable(self):
        cache = _cache_data(_at(2026, 9, 30, 12, 0))
        assert policy.is_focus_usable(cache, "weekly", _at(2026, 10, 5, 4, 0)) is False

    def test_same_week_is_usable(self):
        cache = _cache_data(_at(2026, 9, 30, 12, 0))
        assert policy.is_focus_usable(cache, "weekly", _at(2026, 10, 2, 12, 0)) is True

    def test_monthly_uses_calendar_month(self):
        cache = _cache_data(_at(2026, 3, 20, 12, 0))
        assert policy.is_focus_usable(cache, "monthly", _at(2026, 4, 1, 3, 0)) is False
        assert policy.is_focus_usable(cache, "monthly", _at(2026, 3, 31, 23, 0)) is True

    def test_never_frequency_is_usable(self):
        cache = _cache_data(_at(2020, 1, 1, 0, 0))
        assert policy.is_focus_usable(cache, "never", _at(2026, 10, 5, 12, 0)) is True

    def test_missing_focus_or_time_is_not_usable(self):
        now = _at(2026, 10, 5, 12, 0)
        assert policy.is_focus_usable({}, "weekly", now) is False
        assert policy.is_focus_usable({"focus": {"角色A": {}}}, "weekly", now) is False


class TestCageWeeklyReset:
    def test_reset_follows_configured_hour(self):
        cache = _cache_data(_at(2026, 9, 30, 12, 0), cage=1)
        last_week_key = policy.effective_week_key(_at(2026, 9, 30, 12, 0), 5)
        cache["cage_update_week"] = last_week_key

        # 周一 4 点仍未过刷新时刻，不重置
        assert policy.apply_cage_weekly_reset(cache, _at(2026, 10, 5, 4, 0), 5) is False
        assert cache["focus"]["角色A"]["cage"] == 1

        # 周一 6 点已过刷新时刻，重置为 3
        assert policy.apply_cage_weekly_reset(cache, _at(2026, 10, 5, 6, 0), 5) is True
        assert cache["focus"]["角色A"]["cage"] == 3

    def test_same_week_does_not_reset_twice(self):
        cache = _cache_data(_at(2026, 9, 30, 12, 0), cage=3)
        now = _at(2026, 10, 5, 6, 0)
        assert policy.apply_cage_weekly_reset(cache, now, 5) is True
        assert policy.apply_cage_weekly_reset(cache, now, 5) is False

    def test_later_hour_keeps_previous_week(self):
        cache = _cache_data(_at(2026, 9, 30, 12, 0), cage=3)
        last_week_key = policy.effective_week_key(_at(2026, 9, 30, 12, 0), 14)
        cache["cage_update_week"] = last_week_key
        assert policy.apply_cage_weekly_reset(cache, _at(2026, 10, 5, 6, 0), 14) is False
        assert (
            policy.apply_cage_weekly_reset(cache, _at(2026, 10, 5, 14, 0), 14) is True
        )
