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

"""深谣战斗程序

状态机::

    idle ──p1──► p1_ult / p1_core1 / p1_core2 / p1_farm ──► idle
      └──p2──► p2_ult_charge ──► p2_ult_finish ──► p2_ult_burst ──► switch
            └── p2_ball / p2_farm ──► idle
"""

from __future__ import annotations

from action.combat.core.role import BaseRole

_P1_PHASE = "检查阶段p1_深谣"
_P2_PHASE = "检查阶段p2_深谣"
_CORE1_NODE = "检查核心被动1_深谣"
_CORE2_NODE = "检查核心被动2_深谣"
_P1_FARM_TICKS = 5
_P2_ULT_CHARGE = 10
_P2_ULT_BURST = 10
_P2_FARM_TICKS = 8


class LostLullaby(BaseRole):
    """深谣：p1 核心消球，p2 大招连段后切人。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._farm_ticks = 0
        self._burst_ticks = 0
        self._burst_total = 0

    def reset_state(self) -> None:
        super().reset_state()
        self._farm_ticks = 0
        self._burst_ticks = 0
        self._burst_total = 0

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "p1_ult":
            self._phase_p1_ult()
        elif self.phase == "p1_core1":
            self._phase_p1_core1()
        elif self.phase == "p1_core2":
            self._phase_p1_core2()
        elif self.phase == "p1_farm":
            self._phase_p1_farm()
        elif self.phase == "p2_ball":
            self._phase_p2_ball()
        elif self.phase == "p2_farm":
            self._phase_p2_farm()
        elif self.phase == "p2_ult_charge":
            self._phase_p2_ult_charge()
        elif self.phase == "p2_ult_finish":
            self._phase_p2_ult_finish()
        elif self.phase == "p2_ult_burst":
            self._phase_p2_ult_burst()
        elif self.phase == "switch":
            self._phase_switch()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _in_p1(self) -> bool:
        return bool(self.action.check_status(_P1_PHASE))

    def _in_p2(self) -> bool:
        return bool(self.action.check_status(_P2_PHASE))

    def _begin_burst(self, total: int, next_phase: str) -> None:
        self._burst_total = total
        self._burst_ticks = 0
        self.phase = next_phase

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        if self._in_p1():
            self.action.logger.debug("深谣: p1")
            if self.action.check_Skill_energy_bar():
                self.phase = "p1_ult"
                return
            if self.action.check_status(_CORE1_NODE):
                self.phase = "p1_core1"
                return
            if self.action.check_status(_CORE2_NODE):
                self.phase = "p1_core2"
                return
            self._farm_ticks = 0
            self.phase = "p1_farm"
            return

        if self._in_p2():
            self.action.logger.debug("深谣: p2")
            if self.action.check_Skill_energy_bar():
                self._begin_burst(_P2_ULT_CHARGE, "p2_ult_charge")
                return
            self.phase = "p2_ball"
            return

    def _phase_p1_ult(self) -> None:
        self.action.attack()
        self.action.use_skill()
        self.action.auxiliary_machine()
        self.phase = "idle"

    def _phase_p1_core1(self) -> None:
        self.action.attack()
        self.action.logger.info("深谣: p1核心被动1")
        self.action.ball_elimination_target(1)
        self.action.dodge()
        self.phase = "idle"

    def _phase_p1_core2(self) -> None:
        self.action.logger.info("深谣: p1核心被动2")
        self.action.attack()
        self.action.ball_elimination_target(1)
        self.phase = "idle"

    def _phase_p1_farm(self) -> None:
        self.action.ball_elimination_target(2)
        self.action.attack()
        self._farm_ticks += 1
        if self._farm_ticks >= _P1_FARM_TICKS:
            self.phase = "idle"

    def _phase_p2_ball(self) -> None:
        self.action.ball_elimination_target(1)
        self.action.ball_elimination_target(2)
        self._farm_ticks = 0
        self.phase = "p2_farm"

    def _phase_p2_farm(self) -> None:
        self.action.attack()
        self._farm_ticks += 1
        if self._farm_ticks >= _P2_FARM_TICKS:
            self.phase = "idle"

    def _phase_p2_ult_charge(self) -> None:
        self.action.ball_elimination_target(1)
        self.action.attack()
        self._burst_ticks += 1
        if self._burst_ticks >= self._burst_total:
            self.phase = "p2_ult_finish"

    def _phase_p2_ult_finish(self) -> None:
        self.action.long_press_attack()
        self.action.logger.info("深谣: 毁灭吧")
        self._begin_burst(_P2_ULT_BURST, "p2_ult_burst")

    def _phase_p2_ult_burst(self) -> None:
        self.action.attack()
        self.action.use_skill()
        self.action.auxiliary_machine()
        self._burst_ticks += 1
        if self._burst_ticks >= self._burst_total:
            self.action.logger.info("深谣: 沉没在这片海底")
            self.phase = "idle"  # switch

    def _phase_switch(self) -> None:
        # if self.switch_next():
        #     self.action.logger.info("深谣: 切换完成")
        self.phase = "idle"
