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

"""卡列尼娜·烬航战斗程序

状态机（每 tick 先认 p1 普攻键，未命中再认 p2；p2 有时限）::

    idle ──► combat
      [p1] 大招 ──► ult ──► QTE ──► 切人
      [p1] 核心条 ──► 长按闪避 700ms ──► 盲发普攻 1s
      [p1] 球≥3 ──► 消 2 号球
      [p1] 兜底 ──► 普攻

      [p2] 核心条 ──► 长按攻击 ──► 盲发普攻 1s
      [p2] 大招 ──► ult ──► QTE ──► 切人
      [p2] 兜底 ──► 普攻

Pipeline：Check_Characters_Skill/Effulgence.jsonc
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_P1_NODE = "检查阶段p1_烬航"
_P2_NODE = "检查阶段p2_烬航"
_P1_CORE_BAR_NODE = "检查p1核心条_烬航"
_P2_CORE_BAR_NODE = "检查p2核心条_烬航"

_BALL_MIN = 3
_OVERFLOW_BALL = 2
_P1_DODGE_MS = 700
_P2_ATTACK_MS = 1000
_FOLLOW_ATTACK_MS = 1000


class Effulgence(BaseRole):
    """烬航：p1 放大切人 / 长闪进 p2；p2 每 tick 重识别，核心条长按攻击。"""

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "ult":
            self._phase_ult()
        elif self._in_p1():
            self._phase_p1()
        elif self._in_p2():
            self._phase_p2()
        else:
            self._phase_p1()

    def _in_p1(self) -> bool:
        return bool(self.action.check_status(_P1_NODE))

    def _in_p2(self) -> bool:
        return bool(self.action.check_status(_P2_NODE))

    def _has_p1_core_bar(self) -> bool:
        return bool(self.action.check_status(_P1_CORE_BAR_NODE))

    def _has_p2_core_bar(self) -> bool:
        return bool(self.action.check_status(_P2_CORE_BAR_NODE))

    def _blind_attack(self, duration_ms: int = _FOLLOW_ATTACK_MS) -> None:
        deadline = time.monotonic() + duration_ms / 1000
        while time.monotonic() < deadline:
            if self.combat.context.tasker.stopping:
                return
            self.action.attack()

    def _try_enter_ult(self) -> bool:
        if not self.action.check_Skill_energy_bar():
            return False
        self.phase = "ult"
        return True

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.phase = "combat"

    def _phase_ult(self) -> None:
        stage = "p2" if self._in_p2() else "p1"
        self.action.logger.info("烬航: %s 大招", stage)
        if not self.action.use_skill_until_empty():
            self.action.logger.warning("烬航: %s 大招未确认释放", stage)
            self.phase = "combat"
            return

        self.action.logger.info("烬航: 大招结束，QTE 切人")
        self.action.use_qte()
        self.combat.request_role_switch(self)

    def _phase_p1(self) -> None:
        if self._try_enter_ult():
            return

        if self._has_p1_core_bar():
            self.action.logger.info("烬航: p1 核心条，长按闪避 %dms 进 p2", _P1_DODGE_MS)
            self.action.long_press_dodge(_P1_DODGE_MS)
            self._blind_attack()
            return

        if self.action.count_signal_balls() >= _BALL_MIN:
            self.action.logger.info("烬航: p1 球≥%d，消 %d 号球", _BALL_MIN, _OVERFLOW_BALL)
            self.action.ball_elimination_target(_OVERFLOW_BALL)
            return

        self.action.attack()

    def _phase_p2(self) -> None:
        if self._has_p2_core_bar():
            self.action.logger.info("烬航: p2 核心条，长按攻击 %dms", _P2_ATTACK_MS)
            self.action.long_press_attack(_P2_ATTACK_MS)
            self._blind_attack()
            return

        if self._try_enter_ult():
            return

        self.action.attack()

    def on_switch_failed(self) -> None:
        self.phase = "combat"
