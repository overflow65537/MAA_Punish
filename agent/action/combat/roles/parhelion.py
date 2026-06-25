# Copyright (c) 2024-2025 MAA_Punish
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""幻日战斗程序

状态机（p1/p2 由 ``检查阶段p1_幻日`` / ``检查阶段p2_幻日`` 区分；消球计数基准 4）::

    idle ──► combat
      [p1] 大招 ──► QTE ──► p2 UI（p2 大招判定冷却）
      [p1] 球≥6 ──► p1_ball2（每组：消4×2→长按闪避，组内原子执行）
      [p1] 兜底 ──► 普攻连段

      [p2] 1 号球未 CD ──► 消 1 号球 ──► return（21s CD）
      [p2] 大招 ──► QTE ──► 切人
      [p2] 特殊攻击 ──► 长按闪避 700ms
      [p2] 核心条 ──► 连点闪避 4.5s
      [p2] 球≥6 ──► p2_ball2（消 4 号球，不接闪避）
      [p2] 兜底 ──► 普攻连段

Pipeline：Check_Characters_Skill/Parhelion.jsonc
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole
from action.combat.timing import active_delay

_P1_PHASE_NODE = "检查阶段p1_幻日"
_P2_PHASE_NODE = "检查阶段p2_幻日"
_P2_SPECIAL_NODE = "检查p2特殊攻击_幻日"
_P2_CORE_BAR_NODE = "检查p2核心条_幻日"

_BALL1_CD_S = 21.0
_BALL1_SLOT = 1
_BALL_CLEAR_SLOT = 4
_BALL_COUNT_BASE = 4
_BALL2_MIN = 6
_MAX_P1_BALL2_DODGES = 2
_BALL_CLEAR_GAP_S = 0.015
_DODGE_HOLD_MS = 700
_P2_CORE_DODGE_S = 4.5
_P2_ULT_GRACE_S = 3.0
_ATTACK_BURST = 5
_ATTACK_INTERVAL_MS = 50


class Parhelion(BaseRole):
    """幻日：p1 消 4 号球连段；p2 消 1 号球（21s CD）+ 收尾大招切人。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ball1_last_at = 0.0
        self._p1_ult_finished_at = 0.0
        self._p1_ball2_batches: list[tuple[str, ...]] = []
        self._p2_ball2_batches: list[tuple[str, ...]] = []

    def reset_state(self) -> None:
        super().reset_state()
        self._ball1_last_at = 0.0
        self._p1_ult_finished_at = 0.0
        self._p1_ball2_batches = []
        self._p2_ball2_batches = []

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "p1_ult":
            self._phase_p1_ult()
        elif self.phase == "p1_ball2":
            self._phase_p1_ball2()
        elif self.phase == "p2_ball2":
            self._phase_p2_ball2()
        elif self.phase == "p2_ult":
            self._phase_p2_ult()
        elif self._in_p2():
            self._phase_p2()
        elif self._in_p1():
            self._phase_p1()
        else:
            self._phase_p1()

    def _in_p1(self) -> bool:
        return bool(self.action.check_status(_P1_PHASE_NODE))

    def _in_p2(self) -> bool:
        return bool(self.action.check_status(_P2_PHASE_NODE))

    def _p2_ult_on_grace(self) -> bool:
        """p1 大招 + QTE 后短暂忽略 p2 大招条，避免能量残留误触 p2 大招。"""
        if self._p1_ult_finished_at <= 0:
            return False
        return time.monotonic() - self._p1_ult_finished_at < _P2_ULT_GRACE_S

    def _attack_burst(self) -> None:
        self.action.continuous_attack(_ATTACK_BURST, _ATTACK_INTERVAL_MS)

    def _ball1_ready(self) -> bool:
        if not self._in_p2():
            return False
        if self._ball1_last_at <= 0:
            return True
        return time.monotonic() - self._ball1_last_at >= _BALL1_CD_S

    def _try_consume_ball1(self) -> bool:
        if not self._ball1_ready():
            return False
        self.action.logger.info("幻日: p2 消 1 号球")
        self.action.ball_elimination_target(_BALL1_SLOT)
        self._ball1_last_at = time.monotonic()
        return True

    def _ball2_clear_count(self, ball_count: int) -> int:
        """可消球次数：OCR 球数减去基准 4，再按 (n-4)//2+1 换算点击次数。"""
        if ball_count < _BALL2_MIN:
            return 0
        return (ball_count - _BALL_COUNT_BASE) // 2 + 1

    def _build_p1_ball2_batches(self, ball_count: int) -> list[tuple[str, ...]]:
        """每组：消 4 号球×2 → 长按闪避；余 1 次则 消 4×1 → 长按闪避（组内不拆开）。"""
        clear_count = self._ball2_clear_count(ball_count)
        if clear_count <= 0:
            return []

        pairs = clear_count // 2
        remainder = clear_count % 2
        batches: list[tuple[str, ...]] = []
        dodges = 0

        for _ in range(pairs):
            if dodges < _MAX_P1_BALL2_DODGES:
                batches.append(("clear", "clear", "dodge"))
                dodges += 1
            else:
                batches.append(("clear", "clear"))

        if remainder:
            if dodges < _MAX_P1_BALL2_DODGES:
                batches.append(("clear", "dodge"))
            else:
                batches.append(("clear",))

        return batches

    def _build_p2_ball2_batches(self, ball_count: int) -> list[tuple[str, ...]]:
        clear_count = self._ball2_clear_count(ball_count)
        if clear_count <= 0:
            return []
        return [("clear",) * clear_count]

    def _run_ball2_batch(self, batch: tuple[str, ...]) -> None:
        prev: str | None = None
        for step in batch:
            if step == "clear":
                if prev == "clear":
                    time.sleep(_BALL_CLEAR_GAP_S)
                self.action.ball_elimination_target(_BALL_CLEAR_SLOT)
            elif step == "dodge":
                self.action.long_press_dodge(_DODGE_HOLD_MS)
            prev = step

    def _format_ball2_batches(self, batches: list[tuple[str, ...]]) -> str:
        return " | ".join("+".join(batch) for batch in batches)

    def _start_p1_ball2(self, ball_count: int) -> bool:
        batches = self._build_p1_ball2_batches(ball_count)
        if not batches:
            return False

        self.action.logger.info(
            "幻日: p1 消 4 号球 batches=%s balls=%d clears=%d",
            self._format_ball2_batches(batches),
            ball_count,
            self._ball2_clear_count(ball_count),
        )
        self._p1_ball2_batches = batches
        self.phase = "p1_ball2"
        return True

    def _start_p2_ball2(self, ball_count: int) -> bool:
        batches = self._build_p2_ball2_batches(ball_count)
        if not batches:
            return False

        self.action.logger.info(
            "幻日: p2 消 4 号球 batches=%s balls=%d clears=%d",
            self._format_ball2_batches(batches),
            ball_count,
            self._ball2_clear_count(ball_count),
        )
        self._p2_ball2_batches = batches
        self.phase = "p2_ball2"
        return True

    def _phase_p1_ball2(self) -> None:
        if self._in_p2():
            self._p1_ball2_batches = []
            self.phase = "combat"
            return

        if self.action.check_Skill_energy_bar():
            self._p1_ball2_batches = []
            self.phase = "p1_ult"
            return

        if not self._p1_ball2_batches:
            self.phase = "combat"
            return

        self._run_ball2_batch(self._p1_ball2_batches.pop(0))

        if not self._p1_ball2_batches:
            self.phase = "combat"

    def _phase_p2_ball2(self) -> None:
        if not self._in_p2():
            self._p2_ball2_batches = []
            self.phase = "combat"
            return

        if self.action.check_Skill_energy_bar() and not self._p2_ult_on_grace():
            self._p2_ball2_batches = []
            self.phase = "p2_ult"
            return

        if not self._p2_ball2_batches:
            self.phase = "combat"
            return

        self._run_ball2_batch(self._p2_ball2_batches.pop(0))

        if not self._p2_ball2_batches:
            self.phase = "combat"

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.phase = "combat"

    def _phase_p1(self) -> None:
        if not self._in_p1() and self._in_p2():
            return

        if self.action.check_Skill_energy_bar():
            self.phase = "p1_ult"
            return

        ball_count = self.action.count_signal_balls()
        if ball_count >= _BALL2_MIN and self._start_p1_ball2(ball_count):
            self._phase_p1_ball2()
            return

        self._attack_burst()

    def _phase_p1_ult(self) -> None:
        if self._in_p2():
            self.phase = "combat"
            return

        self.action.logger.info("幻日: p1 大招")
        if not self.action.use_skill_until_empty():
            self.action.logger.warning("幻日: p1 大招未确认释放")
            self.phase = "combat"
            return

        self.action.logger.info("幻日: p1 大招结束，QTE 等待 p2 UI")
        self.action.auxiliary_machine()
        self.action.use_qte()
        self._p1_ult_finished_at = time.monotonic()
        self.phase = "combat"

    def _phase_p2(self) -> None:
        if self._try_consume_ball1():
            return

        if self.action.check_Skill_energy_bar():
            if self._p2_ult_on_grace():
                self.action.logger.debug("幻日: p2 大招冷却中，跳过")
                self._attack_burst()
                return
            self.phase = "p2_ult"
            return

        if self.action.check_status(_P2_SPECIAL_NODE):
            self.action.logger.info("幻日: p2 特殊攻击")
            self.action.long_press_dodge(_DODGE_HOLD_MS)
            return

        if self.action.check_status(_P2_CORE_BAR_NODE):
            self.action.logger.info("幻日: p2 核心条连闪")
            active_delay(
                _P2_CORE_DODGE_S,
                on_tick=self.action.dodge,
                should_stop=lambda: self.combat.context.tasker.stopping,
            )
            return

        ball_count = self.action.count_signal_balls()
        if ball_count >= _BALL2_MIN and self._start_p2_ball2(ball_count):
            self._phase_p2_ball2()
            return

        self._attack_burst()

    def _phase_p2_ult(self) -> None:
        if not self._in_p2():
            self.phase = "combat"
            return

        if self._p2_ult_on_grace():
            self.phase = "combat"
            return

        self.action.logger.info("幻日: p2 大招")
        if not self.action.use_skill_until_empty():
            self.action.logger.warning("幻日: p2 大招未确认释放")
            self.phase = "combat"
            return

        self.action.logger.info("幻日: p2 大招结束，QTE 切人")
        self.action.auxiliary_machine()
        self.action.use_qte()
        self.combat.request_role_switch(self)

    def on_switch_failed(self) -> None:
        self.phase = "combat"
