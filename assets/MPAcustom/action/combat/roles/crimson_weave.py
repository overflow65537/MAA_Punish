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

from __future__ import annotations

import time

from MPAcustom.action.combat.core.role import BaseRole


class CrimsonWeaveRole(BaseRole):
    def __init__(self, combat, color: str, cls_name: str):
        super().__init__(combat, color, cls_name)
        self._loop_idx = 0
        self._burst_idx = 0
        self._ball_idx = 0
        self._dragon_step = 0
        self._deadline: float | None = None
        self._loop_ready_at: float | None = None

    def reset_state(self) -> None:
        super().reset_state()
        self._loop_idx = 0
        self._burst_idx = 0
        self._ball_idx = 0
        self._dragon_step = 0
        self._deadline = None
        self._loop_ready_at = None

    def do_perform(self) -> None:
        if self.phase == "idle":
            self.action.lens_lock()
            self.action.attack()
            if self.action.get_hp_percent() >= 70:
                self.phase = "high_dodge"
            else:
                self.phase = "low_down"
            return

        if self.phase == "done":
            self.phase = "idle"
            return

        if self.phase == "tail":
            self.action.attack()
            self.phase = "idle"
            return

        if self.phase == "high_dodge":
            self.action.dodge()
            self._loop_idx = 0
            self._loop_ready_at = None
            self.phase = "high_loop"
            return

        if self.phase == "high_loop":
            self._tick_high_loop()
            return

        if self.phase == "high_p1_burst":
            self._tick_burst(combo_qte=True)
            return

        if self.phase == "high_dragon":
            self._tick_dragon(switch_on_finish=True, tail_after_switch=False)
            return

        if self.phase == "low_down":
            self.action.down_dodge()
            self._deadline = time.monotonic() + 1.5
            self.phase = "low_wait"
            return

        if self.phase == "low_wait":
            if self._deadline is not None and time.monotonic() < self._deadline:
                return
            if not self.action.check_status("检查无光值_囚影"):
                self.phase = "low_p1_up"
            else:
                self.phase = "low_p2_up"
            return

        if self.phase == "low_p1_up":
            self.action.up_dodge()
            if self.action.check_Skill_energy_bar():
                self._burst_idx = 0
                self.phase = "low_p1_burst"
            else:
                self.phase = "tail"
            return

        if self.phase == "low_p1_burst":
            self._tick_burst(combo_qte=False, with_aux=True)
            return

        if self.phase == "low_p2_up":
            self.action.up_dodge()
            self._dragon_step = 0
            self._burst_idx = 0
            self._ball_idx = 0
            self.phase = "low_dragon"
            return

        if self.phase == "low_dragon":
            self._tick_dragon(switch_on_finish=True, tail_after_switch=True)
            return

        # main 兜底：开启新一轮
        self.phase = "idle"

    def _light_less_value(self) -> int:
        light_less = self.action.check_status("检查无光值_囚影")
        if light_less and light_less.best_result.text.isdigit():  # type: ignore
            return int(light_less.best_result.text)  # type: ignore
        return -1

    def _tick_high_loop(self) -> None:
        if self._loop_ready_at is not None and time.monotonic() < self._loop_ready_at:
            return

        loop_start = time.monotonic()
        self.action.attack()
        light_less_value = self._light_less_value()

        if light_less_value == -1:
            if self.action.check_Skill_energy_bar():
                self._burst_idx = 0
                self.phase = "high_p1_burst"
                return
        elif light_less_value == 300 or light_less_value >= 474:
            self._dragon_step = 0
            self._burst_idx = 0
            self._ball_idx = 0
            self.phase = "high_dragon"
            return

        self._loop_idx += 1
        if self._loop_idx >= 7:
            self.phase = "tail"
            return

        elapsed = time.monotonic() - loop_start
        self._loop_ready_at = time.monotonic() + max(0.0, 0.3 - elapsed)

    def _tick_burst(
        self, *, combo_qte: bool, with_aux: bool = False
    ) -> None:
        self.action.use_skill()
        self.action.ball_elimination_target(1)
        self._burst_idx += 1
        if self._burst_idx >= 10:
            if with_aux:
                self.action.auxiliary_machine()
            if combo_qte:
                self.action.auto_qte("a")
            self.phase = "tail"

    def _tick_dragon(self, *, switch_on_finish: bool, tail_after_switch: bool = False) -> None:
        if self._dragon_step == 0:
            self.action.long_press_dodge(1500)
            self._dragon_step = 1
            return
        if self._dragon_step == 1:
            self.action.auto_qte("a")
            self._dragon_step = 2
            return
        if self._dragon_step == 2:
            self.action.long_press_attack(2300)
            if self.action.check_Skill_energy_bar():
                self._burst_idx = 0
                self._dragon_step = 3
            else:
                self._ball_idx = 0
                self._dragon_step = 4
            return
        if self._dragon_step == 3:
            self.action.use_skill()
            self._burst_idx += 1
            if self._burst_idx >= 10:
                self.action.auxiliary_machine()
                self._ball_idx = 0
                self._dragon_step = 4
            return
        if self._dragon_step == 4:
            self.action.ball_elimination_target(1)
            self._ball_idx += 1
            if self._ball_idx >= 10:
                self._dragon_step = 5
            return
        if self._dragon_step == 5:
            if switch_on_finish:
                self.action.switch()
            self.phase = "tail" if tail_after_switch else "done"
