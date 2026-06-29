"""战斗场次统计：CombatTask 生命周期内收集，战斗结束写入 combat.log。"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from action.combat.core.role import format_color_label, resolve_cls_label
from action.combat.core.team import TEAM_COLORS, TeamSnapshot


def format_team_line(team: TeamSnapshot) -> str:
    """R/B/Y 策略名 + 当前主站色位，供汇总一行展示。"""
    parts: list[str] = []
    for color in TEAM_COLORS:
        cls_name = team.cls_at(color)
        if cls_name:
            parts.append(
                f"{format_color_label(color)}:{resolve_cls_label(cls_name)}"
            )
    cur = format_color_label(team.current.upper())
    body = " ".join(parts) if parts else "单人"
    return f"{body} @{cur}"


@dataclass
class CombatMetrics:
    start_time: float
    team_line: str = ""
    loop_count: int = 0
    total_attacks: int = 0
    total_switches: int = 0
    switch_skips: int = 0
    switch_failures: int = 0
    total_skill_presses: int = 0
    total_ball_clears: int = 0
    total_dodges: int = 0
    total_qte: int = 0
    end_reason: str = ""
    clear_time: float | None = field(default=None, init=False)

    def inc_attack(self, n: int = 1) -> None:
        self.total_attacks += n

    def inc_switch(self, n: int = 1) -> None:
        self.total_switches += n

    def inc_switch_skip(self, n: int = 1) -> None:
        self.switch_skips += n

    def inc_switch_failure(self, n: int = 1) -> None:
        self.switch_failures += n

    def inc_skill(self, n: int = 1) -> None:
        self.total_skill_presses += n

    def inc_ball_clear(self, n: int = 1) -> None:
        self.total_ball_clears += n

    def inc_dodge(self, n: int = 1) -> None:
        self.total_dodges += n

    def inc_qte(self, n: int = 1) -> None:
        self.total_qte += n

    def finalize(self, reason: str, loop_count: int) -> None:
        self.end_reason = reason
        self.loop_count = loop_count
        self.clear_time = max(0.0, time.monotonic() - self.start_time)

    def format_summary(self) -> list[str]:
        duration = self.clear_time if self.clear_time is not None else 0.0
        lines = [
            "======== 战斗统计 ========",
            (
                f"时长: {duration:.1f}s | 循环: {self.loop_count} | "
                f"退战: {self.end_reason}"
            ),
        ]
        if self.team_line:
            lines.append(f"队伍: {self.team_line}")
        lines.append(
            "攻击: %d | 大招: %d | 消球: %d | 闪避: %d | QTE: %d | 切人: %d"
            % (
                self.total_attacks,
                self.total_skill_presses,
                self.total_ball_clears,
                self.total_dodges,
                self.total_qte,
                self.total_switches,
            )
        )
        if self.switch_skips or self.switch_failures:
            lines.append(
                f"切人跳过: {self.switch_skips} | 切人失败: {self.switch_failures}"
            )
        lines.append("==========================")
        return lines

    def log_summary(self, logger: logging.Logger) -> None:
        for line in self.format_summary():
            logger.info(line)
