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

"""骇影战斗程序

状态机::

    idle ──二阶段──► p2_red ──► p2_yellow ──► p2_blue ──► switch
      ├──球≥9──► p1_clear ──► p1_ult ──► idle
      └──兜底──► p1_farm ──► idle
"""

from __future__ import annotations

from action.combat.core.role import BaseRole

_P2_NODE = "检查骇影2阶段"
_P1_CLEAR_BALL_MIN = 9
_P1_LOOP_MAX = 100
_P2_RED_MAX = 30
_P2_YELLOW_MAX = 20
_P2_BLUE_MAX = 10


class Spectre(BaseRole):
    """骇影：一阶段攒大进二阶段，二阶段 RGB 消球后切人。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._p1_ticks = 0
        self._p2_red_ticks = 0
        self._p2_yellow_ticks = 0
        self._p2_blue_ticks = 0
        self._p2_blue_opened = False

    def reset_state(self) -> None:
        super().reset_state()
        self._p1_ticks = 0
        self._p2_red_ticks = 0
        self._p2_yellow_ticks = 0
        self._p2_blue_ticks = 0
        self._p2_blue_opened = False

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "p1_farm":
            self._phase_p1_farm()
        elif self.phase == "p1_clear":
            self._phase_p1_clear()
        elif self.phase == "p1_ult":
            self._phase_p1_ult()
        elif self.phase == "p2_red":
            self._phase_p2_red()
        elif self.phase == "p2_yellow":
            self._phase_p2_yellow()
        elif self.phase == "p2_blue":
            self._phase_p2_blue()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _in_p2(self) -> bool:
        return self.action.check_status(_P2_NODE)

    def _enter_p2(self) -> None:
        self.action.logger.info("骇影: 二阶段")
        self._p2_red_ticks = 0
        self._p2_yellow_ticks = 0
        self._p2_blue_ticks = 0
        self._p2_blue_opened = False
        self.phase = "p2_red"

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        if self._in_p2():
            self._enter_p2()
            return

        if self.action.count_signal_balls() >= _P1_CLEAR_BALL_MIN:
            self._p1_ticks = 0
            self.phase = "p1_clear"
            return

        self._p1_ticks = 0
        self.phase = "p1_farm"

    def _phase_p1_farm(self) -> None:
        if self._in_p2():
            self._enter_p2()
            return
        if self.action.count_signal_balls() >= _P1_CLEAR_BALL_MIN:
            self._p1_ticks = 0
            self.phase = "p1_clear"
            return

        self.action.attack()
        self._p1_ticks += 1
        if self._p1_ticks >= _P1_LOOP_MAX:
            self.phase = "idle"

    def _phase_p1_clear(self) -> None:
        if self._in_p2():
            self._enter_p2()
            return
        if self.action.check_Skill_energy_bar():
            self.phase = "p1_ult"
            return

        self.action.ball_elimination_target(2)
        self.action.ball_elimination_target(1)
        self.action.attack()
        self._p1_ticks += 1
        if self._p1_ticks >= _P1_LOOP_MAX:
            self.phase = "idle"

    def _phase_p1_ult(self) -> None:
        self.action.logger.info("骇影: 一阶段大招")
        self.action.use_skill()
        self.phase = "idle"

    def _phase_p2_red(self) -> None:
        if self._p2_red_ticks >= _P2_RED_MAX or not self._in_p2():
            self.action.auxiliary_machine()
            self.action.use_qte()
            self._p2_yellow_ticks = 0
            self.phase = "p2_yellow"
            return

        self.action.ball_elimination_target(2)
        self.action.ball_elimination_target(1)
        self._p2_red_ticks += 1

    def _phase_p2_yellow(self) -> None:
        if self._p2_yellow_ticks >= _P2_YELLOW_MAX or not self._in_p2():
            self.action.auxiliary_machine()
            self.action.use_qte()
            self._p2_blue_ticks = 0
            self._p2_blue_opened = False
            self.phase = "p2_blue"
            return

        self.action.attack()
        self.action.ball_elimination_target(1)
        self._p2_yellow_ticks += 1

    def _phase_p2_blue(self) -> None:
        if not self._p2_blue_opened:
            self.action.long_press_attack(1000)
            self._p2_blue_opened = True
            return

        if self._p2_blue_ticks >= _P2_BLUE_MAX or not self._in_p2():
            self.action.auxiliary_machine()
            self.phase = "switch"
            return

        self.action.ball_elimination_target(1)
        self.action.attack()
        self._p2_blue_ticks += 1
