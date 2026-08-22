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

状态机（p2 只作进场标志，不单独作为常驻阶段）::

    idle ──► combat
      大招 ──► ult ──► QTE ──► 切人
      p1 核心条满 ──► 按下闪避 ──► 等到 p2 标志（1.5s 超时）──► 松手
        ──► 普攻最多 6s（命中 p2 核心则长按普攻 700ms）──► 有大招则放，否则回 p1
      球≥3 ──► 普攻 ──► 消 2 号球 ──► 普攻
      兜底 ──► 普攻

Pipeline：Check_Characters_Skill/Effulgence.jsonc
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_P1_CORE_BAR_NODE = "检查p1核心条_烬航"
_P2_NODE = "检查阶段p2_烬航"
_P2_CORE_BAR_NODE = "检查p2核心条_烬航"

_BALL_MIN = 3
_OVERFLOW_BALL = 2
_P2_WAIT_TIMEOUT = 1.5
_BURST_ATTACK_S = 6.0
_BURST_HOLD_MS = 700


class Effulgence(BaseRole):
    """烬航：p1 核心满后按闪避等 p2 标志，松手连段后放大或回 p1。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._p2_wait_deadline = 0.0

    def reset_state(self) -> None:
        super().reset_state()
        self._p2_wait_deadline = 0.0

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            if self.phase == "core_dodge":
                self.action.up_dodge()
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "ult":
            self._phase_ult()
        elif self.phase == "core_dodge":
            self._phase_core_dodge()
        else:
            self._phase_p1()

    def _in_p2(self) -> bool:
        return bool(self.action.check_status(_P2_NODE))

    def _has_p1_core_bar(self) -> bool:
        return bool(self.action.check_status(_P1_CORE_BAR_NODE))

    def _has_p2_core_bar(self) -> bool:
        return bool(self.action.check_status(_P2_CORE_BAR_NODE))

    def _elim_overflow_ball(self) -> None:
        self.action.attack()
        self.action.ball_elimination_target(_OVERFLOW_BALL)
        self.action.attack()

    def _try_enter_ult(self) -> bool:
        if not self.action.check_Skill_energy_bar():
            return False
        self.phase = "ult"
        return True

    def _burst_then_ult_or_p1(self) -> None:
        self.action.logger.info("烬航: 普攻最多 %.0fs，等待 p2 核心", _BURST_ATTACK_S)
        deadline = time.monotonic() + _BURST_ATTACK_S
        core_hit = False
        while time.monotonic() < deadline:
            if self.combat.context.tasker.stopping:
                self.phase = "combat"
                return
            self.action.context.run_action("攻击")
            self.action._invalidate_frame()
            if self._has_p2_core_bar():
                core_hit = True
                break

        if core_hit:
            self.action.logger.info("烬航: p2 核心条，长按普攻 %dms", _BURST_HOLD_MS)
            self.action.long_press_attack(_BURST_HOLD_MS)
            if self.combat.context.tasker.stopping:
                self.phase = "combat"
                return
        else:
            self.action.logger.info("烬航: %.0fs 内未命中 p2 核心", _BURST_ATTACK_S)

        if self._try_enter_ult():
            self._phase_ult()
            return

        self.action.logger.info("烬航: 无大招，回到 p1")
        self.phase = "combat"

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.phase = "combat"

    def _phase_ult(self) -> None:
        self.action.logger.info("烬航: 大招")
        if not self.action.use_skill_until_empty():
            self.action.logger.warning("烬航: 大招未确认释放")
            self.phase = "combat"
            return

        self.action.logger.info("烬航: 大招结束，QTE 切人")
        self.action.use_qte()
        self.combat.request_role_switch(self)

    def _phase_p1(self) -> None:
        if self._try_enter_ult():
            return

        if self._has_p1_core_bar():
            self.action.logger.info("烬航: p1 核心条满，按下闪避等待 p2")
            self.action.down_dodge()
            self._p2_wait_deadline = time.monotonic() + _P2_WAIT_TIMEOUT
            self.phase = "core_dodge"
            return

        if self.action.count_signal_balls() >= _BALL_MIN:
            self.action.logger.info(
                "烬航: p1 球≥%d，消 %d 号球", _BALL_MIN, _OVERFLOW_BALL
            )
            self._elim_overflow_ball()
            return

        self.action.attack()

    def _phase_core_dodge(self) -> None:
        if self._in_p2():
            self.action.up_dodge()
            self.action.logger.info("烬航: p2 标志出现，松开闪避")
            self._burst_then_ult_or_p1()
            return

        if time.monotonic() >= self._p2_wait_deadline:
            self.action.up_dodge()
            self.action.logger.warning("烬航: 等待 p2 标志超时，松开闪避")
            self.phase = "combat"
            return

    def on_switch_failed(self) -> None:
        self.phase = "combat"
        self._p2_wait_deadline = 0.0
