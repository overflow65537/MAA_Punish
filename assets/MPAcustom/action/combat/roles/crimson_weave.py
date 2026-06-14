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

"""
囚影战斗（对齐删除前 exclusives 高血路线）。

形态：无光值 OCR 读不到数字(-1)=小太刀；能读到=大太刀。
小太刀大招满 → 10 连 skill+消球 + QTE。
登龙：仅无光值 300 或 >=474（大招满不触发登龙）。
登龙后：有大则 10 连 skill + 辅机后回 idle；无大则 10 连消球 + 切人（不提前回 idle）。
"""

from __future__ import annotations

import time

from MPAcustom.action.combat.core.role import BaseRole


class CrimsonWeaveRole(BaseRole):
    LOOP_MAX = 7
    LOOP_INTERVAL_S = 0.3
    BURST_COUNT = 10
    BURST_INTERVAL_S = 0.2

    def __init__(self, combat, color: str, cls_name: str):
        super().__init__(combat, color, cls_name)
        self._loop_idx = 0
        self._burst_idx = 0
        self._loop_ready_at: float | None = None
        self._burst_ready_at: float | None = None

    def reset_state(self) -> None:
        super().reset_state()
        self._loop_idx = 0
        self._burst_idx = 0
        self._loop_ready_at = None
        self._burst_ready_at = None

    def do_perform(self) -> None:
        if self.phase == "idle":
            self.action.lens_lock()
            self.action.attack()
            self.phase = "dodge"
        elif self.phase == "dodge":
            self.action.logger.info("闪避")
            self.action.dodge()
            self._loop_idx = 0
            self._loop_ready_at = None
            self.phase = "loop"
        elif self.phase == "loop":
            self._tick_loop()
        elif self.phase == "u1_burst":
            self._tick_u1_burst()
        elif self.phase == "dragon_combo":
            self._tick_dragon_combo()
        elif self.phase == "dragon_skill":
            self._tick_dragon_skill()
        elif self.phase == "dragon_ball":
            self._tick_dragon_ball()
        elif self.phase == "tail":
            self.action.attack()
            self.phase = "idle"
        else:
            self.action.logger.warning("未知 phase=%s，重置 idle", self.phase)
            self.phase = "idle"

    def _tick_loop(self) -> None:
        if self._loop_ready_at is not None and time.monotonic() < self._loop_ready_at:
            return

        loop_start = time.monotonic()
        self.action.attack()
        light = self._light_less_value()
        self.action.logger.debug("loop=%s 无光值=%s", self._loop_idx, light)

        if light == -1:
            if self.action.check_Skill_energy_bar():
                self.action.logger.info("小太刀大招就绪，10 连 skill+消球")
                self._burst_idx = 0
                self._burst_ready_at = None
                self.phase = "u1_burst"
                return
        elif light == 300 or light >= 474:
            self.action.logger.info("登龙就绪 无光值=%s", light)
            self.phase = "dragon_combo"
            return

        self._loop_idx += 1
        if self._loop_idx >= self.LOOP_MAX:
            self.action.logger.debug("loop 结束，收尾普攻")
            self.phase = "tail"
            return

        elapsed = time.monotonic() - loop_start
        self._loop_ready_at = time.monotonic() + max(0.0, self.LOOP_INTERVAL_S - elapsed)

    def _tick_u1_burst(self) -> None:
        if self._burst_ready_at is not None and time.monotonic() < self._burst_ready_at:
            return

        burst_start = time.monotonic()
        self.action.use_skill()
        self.action.ball_elimination_target(1)
        self._burst_idx += 1
        if self._burst_idx >= self.BURST_COUNT:
            self.action.auto_qte("a")
            self.action.logger.info("小太刀大招完成")
            self.phase = "idle"
            return

        elapsed = time.monotonic() - burst_start
        self._burst_ready_at = time.monotonic() + max(0.0, self.BURST_INTERVAL_S - elapsed)

    def _tick_dragon_combo(self) -> None:
        self.action.logger.info("登龙：长按闪避 + 长按攻击")
        self.action.long_press_dodge(1500)
        self.action.auto_qte("a")
        self.action.long_press_attack(2300)
        self._burst_idx = 0
        self._burst_ready_at = None
        if self.action.check_Skill_energy_bar():
            self.action.logger.info("登龙后大招就绪，10 连 skill")
            self.phase = "dragon_skill"
        else:
            self.action.logger.info("登龙后无大招，消球")
            self.phase = "dragon_ball"

    def _tick_dragon_skill(self) -> None:
        if self._burst_ready_at is not None and time.monotonic() < self._burst_ready_at:
            return

        burst_start = time.monotonic()
        self.action.use_skill()
        self._burst_idx += 1
        if self._burst_idx >= self.BURST_COUNT:
            self.action.auxiliary_machine()
            self.action.logger.info("登龙后大招完成，回 idle")
            self.phase = "idle"
            return

        elapsed = time.monotonic() - burst_start
        self._burst_ready_at = time.monotonic() + max(0.0, self.BURST_INTERVAL_S - elapsed)

    def _tick_dragon_ball(self) -> None:
        if self._burst_ready_at is not None and time.monotonic() < self._burst_ready_at:
            return

        burst_start = time.monotonic()
        self.action.ball_elimination_target(1)
        self._burst_idx += 1
        if self._burst_idx >= self.BURST_COUNT:
            self.action.switch()
            self.action.logger.info("登龙流程结束，切人")
            self.phase = "idle"
            return

        elapsed = time.monotonic() - burst_start
        self._burst_ready_at = time.monotonic() + max(0.0, self.BURST_INTERVAL_S - elapsed)

    def _light_less_value(self) -> int:
        light_less = self.action.check_status("检查无光值_囚影")
        if light_less and light_less.best_result.text.isdigit():  # type: ignore
            return int(light_less.best_result.text)  # type: ignore
        return -1
