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

"""启明战斗程序

状态机::

    idle ──大招条──► ult_open ──► ult_clear ──► ult_close（QTE）──► switch
      ├──球≥9──► clear_smart ──三消──► clear_ball1 ──球空──► 长按攻击 ──► idle
      └──兜底──► farm ──► idle
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_CLEAR_BALL_MIN = 9
_ULT_CLEAR_TIMEOUT = 3.0
_FARM_TICKS = 20


class Shukra(BaseRole):
    """启明：满球智能消球 → 三消后连消 1 号 → 球空长按攻击；双段大后切人。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ult_clear_deadline = 0.0
        self._farm_ticks = 0

    def reset_state(self) -> None:
        super().reset_state()
        self._ult_clear_deadline = 0.0
        self._farm_ticks = 0

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "ult_open":
            self._phase_ult_open()
        elif self.phase == "ult_clear":
            self._phase_ult_clear()
        elif self.phase == "ult_close":
            self._phase_ult_close()
        elif self.phase == "clear_smart":
            self._phase_clear_smart()
        elif self.phase == "clear_ball1":
            self._phase_clear_ball1()
        elif self.phase == "farm":
            self._phase_farm()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _enter_clear(self) -> None:
        self.phase = "clear_smart"

    def _finish_clear_core(self) -> None:
        self.action.logger.info("启明: 球空，长按攻击")
        self.action.long_press_attack()
        self.phase = "idle"

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        if self.action.check_Skill_energy_bar():
            self.phase = "ult_open"
            return

        if self.action.count_signal_balls() >= _CLEAR_BALL_MIN:
            self._enter_clear()
            return

        self._farm_ticks = 0
        self.phase = "farm"

    def _phase_ult_open(self) -> None:
        self.action.use_skill()
        self._ult_clear_deadline = time.monotonic() + _ULT_CLEAR_TIMEOUT
        self.phase = "ult_clear"

    def _phase_ult_clear(self) -> None:
        if time.monotonic() >= self._ult_clear_deadline:
            self.phase = "ult_close"
            return
        self.action.ball_elimination_target(1)

    def _phase_ult_close(self) -> None:
        self.action.use_skill()
        self.action.auxiliary_machine()
        self.action.use_qte()
        self.phase = "switch"

    def _phase_clear_smart(self) -> None:
        if self.action.check_Skill_energy_bar():
            self.phase = "ult_open"
            return

        if self.action.count_signal_balls() == 0:
            self._finish_clear_core()
            return

        target = self.action.Arrange_Signal_Balls("any")
        if target > 0:
            self.action.ball_elimination_target(target)
            self.action.logger.info("启明: 三消")
            self.phase = "clear_ball1"
            return
        if target < 0:
            self.action.ball_elimination_target(abs(target))
            return

    def _phase_clear_ball1(self) -> None:
        if self.action.check_Skill_energy_bar():
            self.phase = "ult_open"
            return

        if self.action.count_signal_balls() == 0:
            self._finish_clear_core()
            return

        self.action.ball_elimination_target(1)

    def _phase_farm(self) -> None:
        if self.action.check_Skill_energy_bar():
            self.phase = "ult_open"
            return
        if self.action.count_signal_balls() >= _CLEAR_BALL_MIN:
            self._enter_clear()
            return

        self.action.attack()
        self._farm_ticks += 1
        if self._farm_ticks >= _FARM_TICKS:
            self.phase = "idle"
