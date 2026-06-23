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

"""誓焰战斗程序

状态机::

    idle ──u1──► u1_farm ──► u1_charge ──► u1_burst ──► idle
      ├──u2──► u2_farm ──► u2_ult（一段大，不切人）──► idle
      └──u3──► u3_farm ──► u3_finish（长按攻击 + 大 + QTE 切人）──► switch
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_U1_NODE = "检查u1_誓焰"
_U2_NODE = "检查u2_誓焰"
_U3_NODE = "检查u3_誓焰"
_U3_MAX_NODE = "检查u3_max"
_P1_BAR_NODE = "检查p1动能条_誓焰"
_U1_FARM_MAX = 100
_U1_BURST_DURATION = 1.5
_U2_FARM_MAX = 20
_U3_FARM_MAX = 20


class Pyroath(BaseRole):
    """誓焰：u1/u2/u3 分阶段状态机。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._farm_ticks = 0
        self._u1_burst_deadline = 0.0

    def reset_state(self) -> None:
        super().reset_state()
        self._farm_ticks = 0
        self._u1_burst_deadline = 0.0

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "u1_farm":
            self._phase_u1_farm()
        elif self.phase == "u1_charge":
            self._phase_u1_charge()
        elif self.phase == "u1_burst":
            self._phase_u1_burst()
        elif self.phase == "u2_farm":
            self._phase_u2_farm()
        elif self.phase == "u2_ult":
            self._phase_u2_ult()
        elif self.phase == "u3_farm":
            self._phase_u3_farm()
        elif self.phase == "u3_finish":
            self._phase_u3_finish()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        if self.action.check_status(_U1_NODE):
            self.action.logger.info("誓焰: u1")
            self._farm_ticks = 0
            self.phase = "u1_farm"
            return
        if self.action.check_status(_U2_NODE):
            self.action.logger.info("誓焰: u2")
            self._farm_ticks = 0
            self.phase = "u2_farm"
            return
        if self.action.check_status(_U3_NODE):
            self.action.logger.info("誓焰: u3")
            self._farm_ticks = 0
            self.phase = "u3_farm"
            return

        self.action.attack()

    def _phase_u1_farm(self) -> None:
        if self.action.check_status(_P1_BAR_NODE) or self._farm_ticks >= _U1_FARM_MAX:
            self.action.logger.info("誓焰: p1 动能条满")
            self.phase = "u1_charge"
            return
        self.action.ball_elimination_target()
        self.action.attack()
        self._farm_ticks += 1

    def _phase_u1_charge(self) -> None:
        self.action.logger.info("誓焰: 汇聚阳炎之光")
        self.action.long_press_skill()
        self._u1_burst_deadline = time.monotonic() + _U1_BURST_DURATION
        self.phase = "u1_burst"

    def _phase_u1_burst(self) -> None:
        if time.monotonic() >= self._u1_burst_deadline:
            self.phase = "idle"
            return
        if self.action.check_status(_P1_BAR_NODE):
            self.action.long_press_attack(700)
        self.action.attack()

    def _phase_u2_farm(self) -> None:
        if self.action.check_Skill_energy_bar() or self._farm_ticks >= _U2_FARM_MAX:
            self.phase = "u2_ult"
            return
        self.action.attack()
        self.action.ball_elimination_target()
        self._farm_ticks += 1

    def _phase_u2_ult(self) -> None:
        self.action.use_skill_until_empty()
        self.phase = "idle"

    def _phase_u3_farm(self) -> None:
        if self.action.check_status(_U3_MAX_NODE) or self._farm_ticks >= _U3_FARM_MAX:
            self.phase = "u3_finish"
            return
        self.action.attack()
        self._farm_ticks += 1

    def _phase_u3_finish(self) -> None:
        self.action.long_press_attack(4000)
        self.action.use_skill_until_empty()
        self.action.auxiliary_machine()
        self.action.use_qte()
        self.phase = "switch"
