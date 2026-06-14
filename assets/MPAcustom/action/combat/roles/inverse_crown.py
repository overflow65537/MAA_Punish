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


class InverseCrownRole(BaseRole):
    def __init__(self, combat, color: str, cls_name: str):
        super().__init__(combat, color, cls_name)
        self._skill_step = 0
        self._skill_burst_count = 0
        self._wait_count = 0
        self._deadline: float | None = None

    def reset_state(self) -> None:
        super().reset_state()
        self._skill_step = 0
        self._skill_burst_count = 0
        self._wait_count = 0
        self._deadline = None

    def do_perform(self) -> None:
        if self.phase == "skill":
            self._tick_skill()
            return
        if self.phase == "special_press":
            self._tick_special_press()
            return
        if self.phase == "special_atk":
            self._tick_special_atk()
            return
        if self.phase == "wait_special":
            self._tick_wait_special()
            return

        # idle：每轮 lock + attack + 决策一次
        self.action.lens_lock()
        self.action.attack()

        if self.action.check_status("检查逆冕能量即将满"):
            self.action.logger.info("大招")
            self._start_skill()
            return

        if self.action.count_signal_balls() >= 16:
            self.action.logger.info("球数满足条件，进行球消")
            self.action.ball_elimination_target()
            return

        if self.action.count_signal_balls() > 7 and self.action.check_status(
            "检查逆冕特殊球"
        ):
            self.action.logger.info("特殊球就绪")
            self.phase = "special_press"
            return

        self.action.logger.info("特殊球未就绪")
        self._wait_count = 0
        self.phase = "wait_special"

    def _start_skill(self) -> None:
        self._skill_step = 0
        self._skill_burst_count = 0
        self._deadline = None
        self.phase = "skill"

    def _tick_special_press(self) -> None:
        self.combat.context.run_action(
            "长按1号球", pipeline_override={"长按1号球": {"duration": 5500}}
        )
        self.action.logger.info("特殊球按下完成")
        self._deadline = time.monotonic() + 5
        self.phase = "special_atk"

    def _tick_special_atk(self) -> None:
        if self.action.check_status("检查逆冕能量即将满") or (
            self._deadline is not None and time.monotonic() >= self._deadline
        ):
            self._start_skill()
            return
        self.action.attack()

    def _tick_wait_special(self) -> None:
        self.action.attack()
        self._wait_count += 1
        if self.action.check_status("检查逆冕特殊球"):
            self.action.logger.info("特殊球就绪")
            self.phase = "idle"
        elif self._wait_count >= 20:
            self.phase = "idle"

    def _tick_skill(self) -> None:
        if self._skill_step == 0:
            cage = self.combat.context.get_node_data("选择角色程序")
            if cage is None:
                cage = False
            else:
                cage = cage.get("attach", {}).get("cage", False)
            self.action.logger.info(f"cage: {cage}")

            if cage:
                self.action.long_press_skill(2000)
                self.phase = "idle"
                return

            if self.action.check_status("检查逆冕能量即将满"):
                self._skill_step = 2
                self._skill_burst_count = 0
            else:
                self._skill_step = 1
                self._deadline = time.monotonic() + 10
            return

        if self._skill_step == 1:
            if self.action.check_status("检查逆冕能量即将满") or (
                self._deadline is not None and time.monotonic() >= self._deadline
            ):
                self._skill_step = 2
                self._skill_burst_count = 0
                return
            self.action.attack()
            return

        if self._skill_step == 2:
            self.action.use_skill()
            self._skill_burst_count += 1
            if self.action.check_status("检查逆冕能量空") or self._skill_burst_count >= 20:
                self.action.long_press_attack(4000)
                self.phase = "idle"
            return
