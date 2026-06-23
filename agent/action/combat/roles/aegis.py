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

"""铮骨战斗程序

状态机::

    idle ──► loop ──► switch
              ├──大招条──► ult ──► loop
              └──球≥3──► combo ──► loop
"""

from __future__ import annotations

from action.combat.core.role import BaseRole

_LOOP_MAX = 10
_COMBO_BALL_MIN = 3
_COMBO_CLEAR_COUNT = 3


class Aegis(BaseRole):
    """铮骨：循环消球/普攻，大招与三连消球穿插 QTE。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._loop_ticks = 0
        self._combo_ball_count = 0
        self._combo_clear_ticks = 0

    def reset_state(self) -> None:
        super().reset_state()
        self._loop_ticks = 0
        self._combo_ball_count = 0
        self._combo_clear_ticks = 0

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "loop":
            self._phase_loop()
        elif self.phase == "ult":
            self._phase_ult()
        elif self.phase == "combo":
            self._phase_combo()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.action.attack()
        self._loop_ticks = 0
        self.phase = "loop"

    def _phase_loop(self) -> None:
        if self._loop_ticks >= _LOOP_MAX:
            self.action.attack()
            self.phase = "switch"
            return

        self.action.ball_elimination_target(1)
        self.action.attack()

        if self.action.check_Skill_energy_bar():
            self.phase = "ult"
            return

        if self.action.count_signal_balls() >= _COMBO_BALL_MIN:
            self._combo_ball_count = self.action.count_signal_balls()
            self._combo_clear_ticks = 0
            self.phase = "combo"
            return

        self._loop_ticks += 1

    def _phase_ult(self) -> None:
        self.action.use_skill_until_empty()
        self.action.use_qte()
        self.action.auxiliary_machine()
        self._loop_ticks += 1
        self.phase = "loop"

    def _phase_combo(self) -> None:
        if self._combo_clear_ticks < _COMBO_CLEAR_COUNT:
            self.action.ball_elimination_target()
            self._combo_clear_ticks += 1
            return

        self.action.use_qte()
        if self.action.count_signal_balls() == self._combo_ball_count:
            self.action.dodge()
            self.action.ball_elimination_target()
        self.action.use_qte()
        self.action.auxiliary_machine()
        self._loop_ticks += 1
        self.phase = "loop"
