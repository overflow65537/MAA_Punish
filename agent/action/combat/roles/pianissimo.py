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

"""希声战斗程序"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_PHASE2_NODE = "检查希声2阶段"
_RED_BALL_NODE = "检查希声红球"
_CLEAR_TIMEOUT = 10.0
_P1_BALL_MIN = 5
_P1_CORE_BURST = 15
_P2_CORE_BURST = 20
_P1_FARM_MAX = 30
_FARM_TICK_MS = 50.0


class Pianissimo(BaseRole):
    """希声：1 阶段攒球 → 2 阶段核心 → 切人。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._clear_deadline = 0.0
        self._burst_ticks = 0
        self._burst_total = 0
        self._farm_ticks = 0
        self._next_farm_at = 0.0

    def reset_state(self) -> None:
        super().reset_state()
        self._clear_deadline = 0.0
        self._burst_ticks = 0
        self._burst_total = 0
        self._farm_ticks = 0
        self._next_farm_at = 0.0

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "p1_farm":
            self._phase_p1_farm()
        elif self.phase == "p1_clear":
            self._phase_p1_clear()
        elif self.phase == "p1_core":
            self._phase_p1_core()
        elif self.phase == "p1_burst":
            self._phase_p1_burst()
        elif self.phase == "p2_clear1":
            self._phase_p2_clear1()
        elif self.phase == "p2_core":
            self._phase_p2_core()
        elif self.phase == "p2_burst":
            self._phase_p2_burst()
        elif self.phase == "p2_clear2":
            self._phase_p2_clear2()
        elif self.phase == "p2_ult":
            self._phase_p2_ult()
        elif self.phase == "p2_dodge":
            self._phase_p2_dodge()
        elif self.phase == "switch":
            self._phase_switch()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _in_phase2(self) -> bool:
        return bool(self.action.check_status(_PHASE2_NODE))

    def _red_ball_ready(self) -> bool:
        return bool(self.action.check_status(_RED_BALL_NODE))

    def _begin_clear(self, *, next_phase: str) -> None:
        self._clear_deadline = time.monotonic() + _CLEAR_TIMEOUT
        self.phase = next_phase

    def _clear_expired(self) -> bool:
        return time.monotonic() >= self._clear_deadline

    def _begin_burst(self, total: int, next_after: str) -> None:
        self._burst_total = total
        self._burst_ticks = 0
        self.phase = next_after

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        if self._in_phase2():
            self.action.logger.info("希声2阶段")
            self._begin_clear(next_phase="p2_clear1")
            return

        if self.action.count_signal_balls() > _P1_BALL_MIN:
            self.action.logger.info("希声1阶段")
            self._begin_clear(next_phase="p1_clear")
            return

        self.action.logger.info("希声1阶段信号球不足")
        self._farm_ticks = 0
        self._next_farm_at = 0.0
        self.phase = "p1_farm"

    def _phase_p1_farm(self) -> None:
        now = time.monotonic()
        if self._next_farm_at and now < self._next_farm_at:
            return

        tick_start = now
        if self._in_phase2() or self.action.count_signal_balls() > _P1_BALL_MIN:
            self.phase = "idle"
            return

        self.action.attack()
        self._farm_ticks += 1
        if self._farm_ticks >= _P1_FARM_MAX:
            self.phase = "idle"
            return

        elapsed_ms = (time.monotonic() - tick_start) * 1000
        wait_ms = max(0.0, _FARM_TICK_MS - elapsed_ms)
        self._next_farm_at = time.monotonic() + wait_ms / 1000

    def _phase_p1_clear(self) -> None:
        if self._in_phase2():
            self.phase = "idle"
            return
        if not self.action.count_signal_balls() or self._clear_expired():
            self.action.logger.info("希声1阶段消球结束")
            self.phase = "p1_core"
            return

        self.action.attack()
        target = self.action.Arrange_Signal_Balls()
        self.action.attack()
        if target == -1:
            target = -2
        self.action.ball_elimination_target(target)
        self.action.logger.debug("希声1阶段消球 target=%s", target)
        self.action.attack()

    def _phase_p1_core(self) -> None:
        self.action.long_press_attack(1000)
        self.action.auto_qte("a")
        self.action.auxiliary_machine()
        self._begin_burst(_P1_CORE_BURST, "p1_burst")

    def _phase_p1_burst(self) -> None:
        self.action.attack()
        self.action.ball_elimination_target(1)
        self.action.use_skill()
        self._burst_ticks += 1
        if self._burst_ticks >= self._burst_total:
            self.phase = "idle"

    def _phase_p2_clear1(self) -> None:
        if self._red_ball_ready():
            self.action.use_skill()
            self.phase = "idle"
            return
        if not self.action.count_signal_balls() or self._clear_expired():
            self.action.logger.info("希声2阶段消球结束")
            self.phase = "p2_core"
            return

        self.action.ball_elimination_target(2)
        self.action.attack()

    def _phase_p2_core(self) -> None:
        self.action.long_press_attack(1000)
        self.action.auto_qte("a")
        self._begin_burst(_P2_CORE_BURST, "p2_burst")

    def _phase_p2_burst(self) -> None:
        self.action.attack()
        self.action.ball_elimination_target(1)
        self.action.ball_elimination_target(2)
        self._burst_ticks += 1
        if self._burst_ticks >= self._burst_total:
            self.action.logger.info("希声2阶段核心结束")
            self._begin_clear(next_phase="p2_clear2")

    def _phase_p2_clear2(self) -> None:
        if self._red_ball_ready():
            self.phase = "p2_ult"
            return
        if not self.action.count_signal_balls() or self._clear_expired():
            self.phase = "p2_dodge"
            return

        self.action.ball_elimination_target(2)
        self.action.attack()

    def _phase_p2_ult(self) -> None:
        self.action.use_skill()
        self.action.auxiliary_machine()
        self.action.auto_qte("a")
        self.phase = "switch"

    def _phase_p2_dodge(self) -> None:
        self.action.long_press_dodge(700)
        self.action.auxiliary_machine()
        self.action.auto_qte("a")
        self.action.use_skill()
        self.action.auxiliary_machine()
        self.action.auto_qte("a")
        self.phase = "switch"

    def _phase_switch(self) -> None:
        if self.switch_next():
            self.action.logger.info("切换完成")
        self.phase = "idle"
