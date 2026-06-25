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

"""神威·不落日战斗程序

状态机（p1=不落日.png，p2=不落日_释能.png）::

    idle ──► combat
      [p1] 大招 ──► ult ──► QTE ──► 切人
      [p1] 核心条 ──► 消 1 号球 ──►（进 p2 UI）
      [p1] 球≥3 ──► 消 2 号球
      [p1] 兜底 ──► 普攻连段

      [p2] 大招 ──► ult ──► QTE ──► 切人
      [p2] p2 核心条 ──► 长按闪避 700ms ──► 长按攻击 1s
      [p2] 球≥3 ──► 消 2 号球
      [p2] 兜底 ──► 普攻连段

Pipeline：Check_Characters_Skill/Aeternion.jsonc
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_P1_NODE = "检查阶段p1_不落日"
_P2_NODE = "检查阶段p2_不落日"
_P1_CORE_BAR_NODE = "检查p1核心条_不落日"
_P2_CORE_BAR_NODE = "检查p2核心条_不落日"

_BALL_MIN = 3
_P1_CORE_BALL = 1
_OVERFLOW_BALL = 2
_P2_DODGE_MS = 700
_P2_ATTACK_MS = 1000
_P2_DODGE_ATTACK_GAP_S = 0.05
_ATTACK_BURST = 8
_FOLLOW_ATTACK_BURST = 3
_ATTACK_INTERVAL_MS = 50


class Aeternion(BaseRole):
    """不落日：p1 核心条消 1 球进 p2；p2 核心条闪避+长按攻击；有大 QTE 切人。"""

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "ult":
            self._phase_ult()
        elif self._in_p2():
            self._phase_p2()
        else:
            self._phase_p1()

    def _in_p2(self) -> bool:
        return bool(self.action.check_status(_P2_NODE))

    def _has_p1_core_bar(self) -> bool:
        return bool(self.action.check_status(_P1_CORE_BAR_NODE))

    def _has_p2_core_bar(self) -> bool:
        return bool(self.action.check_status(_P2_CORE_BAR_NODE))

    def _attack_burst(self, count: int = _ATTACK_BURST) -> None:
        self.action.continuous_attack(count, _ATTACK_INTERVAL_MS)

    def _run_step(self, body) -> None:
        self.action.attack()
        try:
            body()
        finally:
            self.action.attack()

    def _try_enter_ult(self) -> bool:
        if not self.action.check_Skill_energy_bar():
            return False
        self.phase = "ult"
        return True

    def _phase_idle(self) -> None:
        def _body() -> None:
            self.action.lens_lock()
            self.phase = "combat"

        self._run_step(_body)

    def _phase_ult(self) -> None:
        stage = "p2" if self._in_p2() else "p1"

        def _body() -> None:
            self.action.logger.info("不落日: %s 大招", stage)
            if not self.action.use_skill_until_empty():
                self.action.logger.warning("不落日: %s 大招未确认释放", stage)
                self.phase = "combat"
                return

            self.action.logger.info("不落日: 大招结束，QTE 切人")
            self.action.attack()
            self.action.use_qte()
            self.combat.request_role_switch(self)

        self._run_step(_body)

    def _phase_p1(self) -> None:
        self.action.attack()

        if self._try_enter_ult():
            return

        if self._in_p2():
            return

        if self._has_p1_core_bar():

            def _body() -> None:
                self.action.logger.info("不落日: p1 核心条，消 1 号球进 p2")
                self.action.attack()
                self.action.ball_elimination_target(_P1_CORE_BALL)
                self._attack_burst(_FOLLOW_ATTACK_BURST)

            self._run_step(_body)
            return

        self.action.attack()
        if self.action.count_signal_balls() >= _BALL_MIN:

            def _body() -> None:
                self.action.logger.info("不落日: p1 球≥3，消 2 号球")
                self.action.attack()
                self.action.ball_elimination_target(_OVERFLOW_BALL)
                self._attack_burst(_FOLLOW_ATTACK_BURST)

            self._run_step(_body)
            return

        self._run_step(lambda: self._attack_burst())

    def _phase_p2(self) -> None:
        self.action.attack()

        if self._try_enter_ult():
            return

        if self._has_p2_core_bar():

            def _body() -> None:
                self.action.logger.info(
                    "不落日: p2 核心条，长按闪避 %dms + 长按攻击 %dms",
                    _P2_DODGE_MS,
                    _P2_ATTACK_MS,
                )
                self.action.attack()
                self.action.long_press_dodge(_P2_DODGE_MS)
                time.sleep(_P2_DODGE_ATTACK_GAP_S)
                self.action.long_press_attack(_P2_ATTACK_MS)
                self._attack_burst(_FOLLOW_ATTACK_BURST)

            self._run_step(_body)
            return

        self.action.attack()
        if self.action.count_signal_balls() >= _BALL_MIN:

            def _body() -> None:
                self.action.logger.info("不落日: p2 球≥3，消 2 号球")
                self.action.attack()
                self.action.ball_elimination_target(_OVERFLOW_BALL)
                self._attack_burst(_FOLLOW_ATTACK_BURST)

            self._run_step(_body)
            return

        self._run_step(lambda: self._attack_burst())

    def on_switch_failed(self) -> None:
        self.phase = "combat"
