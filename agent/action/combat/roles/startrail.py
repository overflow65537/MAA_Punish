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

"""芒星之迹战斗程序

状态机::

    idle ──► p1
      ├──p2 UI──► 消 1 球 ──► p1
      ├──大招条──► p1_ult（确认释放 → QTE → 切人）
      ├──核心被动──► 消 1 球 → 长按攻击 700ms → 消 1 球 ──► p1
      ├──红球>3──► 三连击消球 ×3 ──► p1
      ├──蓝球>3──► 三连击消球 ×2 ──► p1
      └──兜底──► 连续 4 次普攻 ──► p1

Pipeline 节点（Check_Characters_Skill/Startrail.jsonc）：
    检查阶段p2_芒星之迹、检查核心被动_芒星之迹、
    检查红球大于3_芒星之迹、检查蓝球大于3_芒星之迹
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_P2_NODE = "检查阶段p2_芒星之迹"
_CORE_PASSIVE_NODE = "检查核心被动_芒星之迹"
_RED_BALL_NODE = "检查红球大于3_芒星之迹"
_BLUE_BALL_NODE = "检查蓝球大于3_芒星之迹"

_CORE_HOLD_MS = 700
_TRIPLE_TAP_INTERVAL_S = 0.015
_TRIPLE_TAP_COUNT = 3
_RED_CLEAR_COUNT = 3
_BLUE_CLEAR_COUNT = 2
_P1_ATTACK_BURST = 4
_P1_ATTACK_INTERVAL_MS = 50
_DEFAULT_BALL_SLOT = 1


class Startrail(BaseRole):
    """芒星之迹：p1 循环；大招后 QTE 切人；p2 UI 出现时消球回 p1。"""

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "p1":
            self._phase_p1()
        elif self.phase == "p1_ult":
            self._phase_p1_ult()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _in_p2(self) -> bool:
        return bool(self.action.check_status(_P2_NODE))

    def _has_core_passive(self) -> bool:
        return bool(self.action.check_status(_CORE_PASSIVE_NODE))

    def _red_ball_overflow(self) -> bool:
        return bool(self.action.check_status(_RED_BALL_NODE))

    def _blue_ball_overflow(self) -> bool:
        return bool(self.action.check_status(_BLUE_BALL_NODE))

    def _clear_one_ball(self, slot: int = _DEFAULT_BALL_SLOT) -> None:
        self.action.ball_elimination_target(slot)

    def _triple_tap_clear_ball(self, slot: int = _DEFAULT_BALL_SLOT) -> None:
        """单次消球：三连击，间隔 15ms。"""
        for i in range(_TRIPLE_TAP_COUNT):
            self.action.ball_elimination_target(slot)
            if i + 1 < _TRIPLE_TAP_COUNT:
                time.sleep(_TRIPLE_TAP_INTERVAL_S)

    def _clear_balls_triple_tap(self, count: int, slot: int = _DEFAULT_BALL_SLOT) -> None:
        for _ in range(count):
            self._triple_tap_clear_ball(slot)

    def _run_core_passive_combo(self) -> None:
        self.action.logger.info("芒星之迹: 核心被动")
        self._clear_one_ball()
        self.action.long_press_attack(_CORE_HOLD_MS)
        self._clear_one_ball()

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.phase = "p1"

    def _phase_p1(self) -> None:
        if self._in_p2():
            self.action.logger.info("芒星之迹: p2 UI，消 1 球回 p1")
            self._clear_one_ball()
            return

        if self.action.check_Skill_energy_bar():
            self.phase = "p1_ult"
            return

        if self._has_core_passive():
            self._run_core_passive_combo()
            return

        if self._red_ball_overflow():
            self.action.logger.info("芒星之迹: 红球>3，三连击消 3 球")
            self._clear_balls_triple_tap(_RED_CLEAR_COUNT)
            return

        if self._blue_ball_overflow():
            self.action.logger.info("芒星之迹: 蓝球>3，三连击消 2 球")
            self._clear_balls_triple_tap(_BLUE_CLEAR_COUNT)
            return

        self.action.continuous_attack(_P1_ATTACK_BURST, _P1_ATTACK_INTERVAL_MS)

    def _phase_p1_ult(self) -> None:
        self.action.logger.info("芒星之迹: p1 大招")
        if not self.action.use_skill_until_empty():
            self.action.logger.warning("芒星之迹: p1 大招未确认释放")
            self.phase = "p1"
            return

        self.action.logger.info("芒星之迹: 大招结束，QTE 切人")
        self.action.use_qte()
        self.combat.request_role_switch(self)

    def on_switch_failed(self) -> None:
        self.phase = "p1"
