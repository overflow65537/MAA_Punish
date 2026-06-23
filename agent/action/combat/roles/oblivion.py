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

"""终焉战斗程序

状态机::

    idle ──大招条──► ult_open ──► ult_loop ──► ult_close ──► switch ──► idle
      └──无大──► farm ──► idle
"""

from __future__ import annotations

from action.combat.core.role import BaseRole

_CRESCENT_NODE = "检查残月值_终焉"
_CLEAR_MAX = 5
_FARM_MAX = 30
_ULT_LOOP_MAX = 30
_ULT_FINISH_ATTACK = 10
_SKILL_DELAY_MS = 1000
_CRESCENT_PRESS_MS = 2000


class Oblivion(BaseRole):
    """终焉：攒大 → 大招循环消球 → 二段大 → 切人。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._farm_ticks = 0
        self._ult_ticks = 0
        self._finish_ticks = 0
        self._clear_ticks = 0

    def reset_state(self) -> None:
        super().reset_state()
        self._farm_ticks = 0
        self._ult_ticks = 0
        self._finish_ticks = 0
        self._clear_ticks = 0

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "farm":
            self._phase_farm()
        elif self.phase == "ult_open":
            self._phase_ult_open()
        elif self.phase == "ult_loop":
            self._phase_ult_loop()
        elif self.phase == "ult_close":
            self._phase_ult_close()
        elif self.phase == "switch":
            self._phase_switch()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        if self.action.check_Skill_energy_bar():
            self.phase = "ult_open"
            return

        self._farm_ticks = 0
        self._clear_ticks = 0
        self.phase = "farm"

    def _clear_balls(self) -> None:
        while (
            self.action.count_signal_balls()
            and self._clear_ticks < _CLEAR_MAX
            and not self.action.check_Skill_energy_bar()
        ):
            self.action.ball_elimination_target(1)
            self._clear_ticks += 1
            self.action.attack()
            self.action.use_qte()

    def _crescent_press_if_ready(self) -> None:
        if self.action.check_status(_CRESCENT_NODE) and not self.action.check_Skill_energy_bar():
            self.action.long_press_attack(_CRESCENT_PRESS_MS)

    def _phase_farm(self) -> None:
        if self.action.check_Skill_energy_bar():
            self.phase = "ult_open"
            return
        if self._farm_ticks >= _FARM_MAX:
            self.phase = "idle"
            return

        self._clear_ticks = 0
        self.action.attack()
        self._clear_balls()
        self.action.attack()
        self._crescent_press_if_ready()
        self._farm_ticks += 1

    def _phase_ult_open(self) -> None:
        self.action.use_skill(_SKILL_DELAY_MS)
        self.action.auxiliary_machine()
        self.action.use_qte()
        self._ult_ticks = 0
        self._clear_ticks = 0
        self.phase = "ult_loop"

    def _phase_ult_loop(self) -> None:
        if self.action.check_Skill_energy_bar() or self._ult_ticks >= _ULT_LOOP_MAX:
            self._finish_ticks = 0
            self.phase = "ult_close"
            return

        self._clear_ticks = 0
        self.action.attack()
        self._clear_balls()
        self.action.attack()
        self._crescent_press_if_ready()
        self._ult_ticks += 1

    def _phase_ult_close(self) -> None:
        if self._finish_ticks == 0:
            self.action.use_skill(_SKILL_DELAY_MS)
            self.action.auxiliary_machine()
            self.action.use_qte()
            self._finish_ticks = 1
            return

        self.action.attack()
        self._finish_ticks += 1
        if self._finish_ticks > _ULT_FINISH_ATTACK:
            self.phase = "switch"

    def _phase_switch(self) -> None:
        if self.switch_next():
            self.action.logger.info("终焉: 切换完成")
        self.phase = "idle"
