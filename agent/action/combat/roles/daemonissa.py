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

"""谬影战斗程序

状态机（p2 由 ``检查阶段p2_谬影`` 命中判定；未命中即 p1）::

    idle ──► combat
      [p1] 大招条 ──► p1_ult（确认释放 → QTE）──► 等待 p2 UI
      [p1] 球≥3 ──► 消 1 号位
      [p1] 兜底 ──► 连续 5 次普攻

      [p2] 大招条 ──► p2_ult（确认释放 → QTE → 切人）
      [p2] 球≥3 ──► 消 2 号位 → 消 1 号位（同 tick，每轮一次）
      [p2] 兜底 ──► 连续 5 次普攻

Pipeline：Check_Characters_Skill/Daemonissa.jsonc
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_P2_NODE = "检查阶段p2_谬影"
_BALL_CLEAR_MIN = 3
_ATTACK_BURST = 5
_ATTACK_INTERVAL_MS = 50
_P1_BALL_SLOT = 1
_P2_FIRST_BALL_SLOT = 2
_P2_BALL_GAP_S = 0.015
_P2_SECOND_BALL_SLOT = 1


class Daemonissa(BaseRole):
    """谬影：p1 大+QTE 进 p2；p2 消球后大+QTE 切人。"""

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "p1_ult":
            self._phase_p1_ult()
        elif self.phase == "p2_ult":
            self._phase_p2_ult()
        elif self._in_p2():
            self._phase_p2()
        else:
            self._phase_p1()

    def _in_p2(self) -> bool:
        return bool(self.action.check_status(_P2_NODE))

    def _clear_ball(self, slot: int) -> None:
        self.action.ball_elimination_target(slot)

    def _attack_burst(self) -> None:
        self.action.continuous_attack(_ATTACK_BURST, _ATTACK_INTERVAL_MS)

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.phase = "combat"

    def _phase_p1(self) -> None:
        if self.action.check_Skill_energy_bar():
            self.phase = "p1_ult"
            return

        if self.action.count_signal_balls() >= _BALL_CLEAR_MIN:
            self.action.logger.info("谬影: p1 消球")
            self._clear_ball(_P1_BALL_SLOT)
            return

        self._attack_burst()

    def _phase_p1_ult(self) -> None:
        self.action.logger.info("谬影: p1 大招")
        if not self.action.use_skill_until_empty():
            self.action.logger.warning("谬影: p1 大招未确认释放")
            self.phase = "combat"
            return

        self.action.logger.info("谬影: p1 大招结束，QTE 等待 p2 UI")
        self.action.use_qte()
        self.phase = "combat"

    def _phase_p2(self) -> None:
        if self.action.check_Skill_energy_bar():
            self.phase = "p2_ult"
            return

        if self.action.count_signal_balls() >= _BALL_CLEAR_MIN:
            self.action.logger.info("谬影: p2 消球（2 号位 → 1 号位）")
            self._clear_ball(_P2_FIRST_BALL_SLOT)
            time.sleep(_P2_BALL_GAP_S)
            self._clear_ball(_P2_SECOND_BALL_SLOT)
            return

        self._attack_burst()

    def _phase_p2_ult(self) -> None:
        self.action.logger.info("谬影: p2 大招")
        if not self.action.use_skill_until_empty():
            self.action.logger.warning("谬影: p2 大招未确认释放")
            self.phase = "combat"
            return

        self.action.logger.info("谬影: p2 大招结束，QTE 切人")
        self.action.use_qte()
        self.combat.request_role_switch(self)

    def on_switch_failed(self) -> None:
        self.phase = "combat"
