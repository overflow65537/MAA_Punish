"""Tests for combat metrics and combat log prefix."""

from __future__ import annotations

import logging
import time

from action.combat.core.combat_metrics import CombatMetrics, format_team_line
from action.combat.core.team import TeamSnapshot
from logger_component import LOG_DIR, LoggerComponent


class TestCombatMetrics:
    def test_counters_accumulate(self):
        m = CombatMetrics(start_time=time.monotonic())
        m.inc_attack(3)
        m.inc_skill(2)
        m.inc_ball_clear(1)
        m.inc_dodge(4)
        m.inc_qte(2)
        m.inc_switch(1)
        m.inc_switch_skip(2)
        m.inc_switch_failure(1)
        assert m.total_attacks == 3
        assert m.total_skill_presses == 2
        assert m.total_ball_clears == 1
        assert m.total_dodges == 4
        assert m.total_qte == 2
        assert m.total_switches == 1
        assert m.switch_skips == 2
        assert m.switch_failures == 1

    def test_finalize_sets_duration_and_reason(self):
        start = time.monotonic() - 1.5
        m = CombatMetrics(start_time=start)
        m.team_line = "红:启明 @红"
        m.finalize("combat_end_condition", 100)
        assert m.end_reason == "combat_end_condition"
        assert m.loop_count == 100
        assert m.clear_time is not None
        assert m.clear_time >= 1.0

    def test_format_summary_contains_key_fields(self):
        m = CombatMetrics(start_time=time.monotonic())
        m.team_line = "红:启明 蓝:霁梦 @蓝"
        m.total_attacks = 10
        m.total_skill_presses = 2
        m.total_ball_clears = 3
        m.total_dodges = 1
        m.total_qte = 2
        m.total_switches = 1
        m.finalize("stopped", 5)
        text = "\n".join(m.format_summary())
        assert "======== 战斗统计 ========" in text
        assert "循环: 5" in text
        assert "退战: stopped" in text
        assert "红:启明" in text
        assert "攻击: 10" in text
        assert "切人: 1" in text

    def test_log_summary_writes_to_logger(self, caplog):
        caplog.set_level(logging.INFO)
        m = CombatMetrics(start_time=time.monotonic())
        m.finalize("unknown", 0)
        logger = logging.getLogger("test.combat.metrics")
        m.log_summary(logger)
        assert any("战斗统计" in r.message for r in caplog.records)


class TestFormatTeamLine:
    def test_formats_roster_and_current(self):
        team = TeamSnapshot(R="Shukra", B="Limpidity", Y="", current="B")
        line = format_team_line(team)
        assert "红:" in line
        assert "蓝:" in line
        assert "@蓝" in line


class TestLoggerComponentPrefix:
    def test_combat_prefix_uses_combat_filename(self, tmp_path, monkeypatch):
        monkeypatch.setattr("logger_component.LOG_DIR", str(tmp_path))
        component = LoggerComponent(
            "test_combat", log_prefix="combat", console=False
        )
        component.logger.info("combat probe")
        component.close()
        from datetime import datetime

        date = datetime.now().strftime("%Y%m%d")
        log_path = tmp_path / f"combat_{date}.log"
        assert log_path.is_file()
        assert "combat probe" in log_path.read_text(encoding="utf-8")

    def test_custom_prefix_unchanged(self, tmp_path, monkeypatch):
        monkeypatch.setattr("logger_component.LOG_DIR", str(tmp_path))
        component = LoggerComponent("test_custom")
        component.logger.info("custom probe")
        component.close()
        from datetime import datetime

        date = datetime.now().strftime("%Y%m%d")
        log_path = tmp_path / f"custom_{date}.log"
        assert log_path.is_file()
        assert "custom probe" in log_path.read_text(encoding="utf-8")
