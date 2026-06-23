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

"""霁梦战斗程序

状态机::

    idle ──普攻1+核心条──► p1_core ──► p1_burst ──► idle
      ├──普攻1消球──► p1_clear ──► idle
      ├──普攻2+核心球──► p2_core_wait ──► p2_finish ──► p2_burst ──► switch
      ├──普攻2消球──► p2_clear ──► idle
      └──兜底──► farm ──► idle
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_ATK1_NODE = "检查普攻1_霁梦"
_CORE_BAR_NODE = "检查核心条_霁梦"
_ATK2_NODE = "检查普攻2_霁梦"
_CORE_BALL_NODE = "检查核心球_霁梦"
_CORE_BAR2_NODE = "检查核心条2_霁梦"
_P1_BALL_MIN = 5
_P1_BURST_TICKS = 15
_P2_BURST_TICKS = 15
_P2_CORE_WAIT_TIMEOUT = 5.0
_FARM_MAX = 30


class Limpidity(BaseRole):
    """霁梦：普攻1/2 分流，核心条/核心球触发连段。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._burst_ticks = 0
        self._burst_total = 0
        self._farm_ticks = 0
        self._p2_core_deadline = 0.0

    def reset_state(self) -> None:
        super().reset_state()
        self._burst_ticks = 0
        self._burst_total = 0
        self._farm_ticks = 0
        self._p2_core_deadline = 0.0

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "p1_clear":
            self._phase_p1_clear()
        elif self.phase == "p1_core":
            self._phase_p1_core()
        elif self.phase == "p1_burst":
            self._phase_p1_burst()
        elif self.phase == "p2_clear":
            self._phase_p2_clear()
        elif self.phase == "p2_core_wait":
            self._phase_p2_core_wait()
        elif self.phase == "p2_finish":
            self._phase_p2_finish()
        elif self.phase == "p2_burst":
            self._phase_p2_burst()
        elif self.phase == "farm":
            self._phase_farm()
        elif self.phase == "switch":
            self._phase_switch()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _is_atk1(self) -> bool:
        return bool(self.action.check_status(_ATK1_NODE))

    def _is_atk2(self) -> bool:
        return bool(self.action.check_status(_ATK2_NODE))

    def _begin_burst(self, total: int, next_phase: str) -> None:
        self._burst_total = total
        self._burst_ticks = 0
        self.phase = next_phase

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        if self._is_atk1():
            if self.action.check_status(_CORE_BAR_NODE):
                self.action.logger.info("霁梦: 直面天闪")
                self.phase = "p1_core"
                return
            target = self.action.Arrange_Signal_Balls()
            if target > 0 or self.action.count_signal_balls() >= _P1_BALL_MIN:
                self.phase = "p1_clear"
                return

        if self._is_atk2():
            if self.action.check_status(_CORE_BALL_NODE):
                self.action.logger.info("霁梦: 见证我的意志")
                self._p2_core_deadline = time.monotonic() + _P2_CORE_WAIT_TIMEOUT
                self.phase = "p2_core_wait"
                return
            if self.action.count_signal_balls() != 0:
                self.phase = "p2_clear"
                return

        self._farm_ticks = 0
        self.phase = "farm"

    def _phase_p1_clear(self) -> None:
        target = self.action.Arrange_Signal_Balls()
        self.action.ball_elimination_target(target)
        self.action.attack()
        self.phase = "idle"

    def _phase_p1_core(self) -> None:
        self.action.long_press_dodge(1000)
        self._begin_burst(_P1_BURST_TICKS, "p1_burst")

    def _phase_p1_burst(self) -> None:
        self.action.use_skill()
        self.action.auxiliary_machine()
        self.action.attack()
        self._burst_ticks += 1
        if self._burst_ticks >= self._burst_total:
            self.action.logger.info("霁梦: 以苦厄澈我心镜")
            self.action.attack()
            self.phase = "idle"

    def _phase_p2_clear(self) -> None:
        self.action.ball_elimination_target()
        self.action.attack()
        self.phase = "idle"

    def _phase_p2_core_wait(self) -> None:
        if self.action.check_status(_CORE_BAR2_NODE):
            self.phase = "p2_finish"
            return
        if time.monotonic() >= self._p2_core_deadline:
            self.action.logger.warning("霁梦: 等待核心条2超时")
            self.phase = "idle"
            return
        self.action.ball_elimination_target(1)

    def _phase_p2_finish(self) -> None:
        self.action.long_press_attack(3000)
        self.action.logger.info("霁梦: 终于梦醒时分")
        self._begin_burst(_P2_BURST_TICKS, "p2_burst")

    def _phase_p2_burst(self) -> None:
        self.action.use_skill()
        self.action.auxiliary_machine()
        self._burst_ticks += 1
        if self._burst_ticks >= self._burst_total:
            self.action.logger.info("霁梦: 映天地渡你新生")
            self.phase = "idle"  # switch

    def _phase_farm(self) -> None:
        self.action.attack()
        self._farm_ticks += 1
        if self._farm_ticks >= _FARM_MAX:
            self.phase = "idle"

    def _phase_switch(self) -> None:
        # if self.switch_next():
        #     self.action.logger.info("霁梦: 切换完成")
        self.phase = "idle"
