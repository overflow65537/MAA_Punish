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

"""极锋战斗程序

状态机（p1/p2 由 ``检查阶段p1_极锋`` / ``检查阶段p2_极锋`` 区分）::

    idle ──► combat
      [p1] 大招 ──► QTE ──► 切人
      [p1] 核心被动 ──► 消 1 号球 ──► p2 UI
      [p1] 核心条 ──► 长按攻击 ──► 短普攻
      [p1] 球≥3 ──► 持续消固定球位+高频攻击直至核心条（超时 5s）──► 长按攻击
      [p1] 兜底 ──► 普攻连段

      [p2] 大招 ──► QTE ──► 切人
      [p2] p2 核心条满 ──► 消 3 号球×2 ──► 长按攻击 2.25s
      [p2] 兜底 ──► 消 1 号球 ──► 普攻连段 ──► p1 UI

Pipeline：Check_Characters_Skill/Arete.jsonc
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_P1_PHASE_NODE = "检查阶段p1_极锋"
_P2_PHASE_NODE = "检查阶段p2_极锋"
_CORE_PASSIVE_NODE = "检查核心被动_极锋"
_P1_CORE_BAR_NODE = "检查极锋核心条1"
_P2_CORE_BAR_NODE = "检查p2核心条_极锋"

_P1_BALL_MIN = 3
_P1_TO_P2_BALL = 1
_P2_TO_P1_BALL = 1
_P2_CORE_BALL = 3
_P2_CORE_BALL_CLEAR_COUNT = 2
_P1_ROTATE_BALL_MIN = 2
_P1_ROTATE_BALL_MAX = 4
_P1_CLEAR_TIMEOUT_S = 5.0
_P1_CLEAR_ATTACKS = 2
_P1_CLEAR_CHECK_INTERVAL = 3
_P1_POST_CORE_ATTACK_BURST = 3
_P1_CORE_LONG_PRESS_MS = 800
_P2_CORE_LONG_PRESS_MS = 2250
_ATTACK_BURST = 8
_FOLLOW_ATTACK_BURST = 5
_ATTACK_INTERVAL_MS = 50


class Arete(BaseRole):
    """极锋：p1 核心被动消球进 p2；p2 核心条满消球长按，兜底回 p1。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._p1_rotate_ball_slot = _P1_ROTATE_BALL_MIN

    def _pick_p1_clear_ball_slot(self) -> int:
        slot = self._p1_rotate_ball_slot + 1
        if slot > _P1_ROTATE_BALL_MAX:
            slot = _P1_ROTATE_BALL_MIN
        return slot

    def _advance_p1_clear_ball_slot(self) -> None:
        self._p1_rotate_ball_slot = self._pick_p1_clear_ball_slot()

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
        elif self._in_p1():
            self._phase_p1()
        else:
            self._phase_p1()

    def _in_p1(self) -> bool:
        return bool(self.action.check_status(_P1_PHASE_NODE))

    def _in_p2(self) -> bool:
        return bool(self.action.check_status(_P2_PHASE_NODE))

    def _attack_burst(self, count: int = _ATTACK_BURST) -> None:
        self.action.continuous_attack(count, _ATTACK_INTERVAL_MS)

    def _run_step(self, body) -> None:
        self.action.attack()
        try:
            body()
        finally:
            self.action.attack()

    def _p1_core_long_press(self) -> None:
        def _body() -> None:
            self.action.logger.info("极锋: p1 核心条，长按攻击")
            self.action.long_press_attack(_P1_CORE_LONG_PRESS_MS)
            self._attack_burst(_P1_POST_CORE_ATTACK_BURST)

        self._run_step(_body)

    def _p1_clear_until_core_bar(self) -> None:
        clear_slot = self._pick_p1_clear_ball_slot()
        deadline = time.monotonic() + _P1_CLEAR_TIMEOUT_S

        def _body() -> None:
            self.action.logger.info(
                "极锋: p1 持续消 %d 号球直至核心条（超时 %.0fs）",
                clear_slot,
                _P1_CLEAR_TIMEOUT_S,
            )
            loop_tick = 0
            while time.monotonic() < deadline:
                self.action.attack()
                if loop_tick % _P1_CLEAR_CHECK_INTERVAL == 0:
                    if self.combat.context.tasker.stopping:
                        return
                    if self.action.check_Skill_energy_bar():
                        self.phase = "p1_ult"
                        return
                    if self.action.check_status(_CORE_PASSIVE_NODE):
                        self.action.logger.info("极锋: p1 核心被动，消 1 号球进 p2")
                        self.action.ball_elimination_target(_P1_TO_P2_BALL)
                        return
                    if not self._in_p1() and self._in_p2():
                        return
                if self.action.check_status(_P1_CORE_BAR_NODE):
                    self._p1_core_long_press()
                    return

                self.action.ball_elimination_target(clear_slot)
                for _ in range(_P1_CLEAR_ATTACKS):
                    self.action.attack()
                loop_tick += 1

            self.action.logger.warning("极锋: p1 消球超时 %.0fs", _P1_CLEAR_TIMEOUT_S)

        try:
            self._run_step(_body)
        finally:
            self._advance_p1_clear_ball_slot()

    def _finish_ult_and_switch(self, *, stage: str) -> None:
        def _body() -> None:
            self.action.logger.info("极锋: %s 大招", stage)
            if not self.action.use_skill_until_empty():
                self.action.logger.warning("极锋: %s 大招未确认释放", stage)
                self.phase = "combat"
                return

            self.action.logger.info("极锋: %s 大招结束，QTE 切人", stage)
            self.action.use_qte()
            self.combat.request_role_switch(self)

        self._run_step(_body)

    def _phase_idle(self) -> None:
        def _body() -> None:
            self.action.lens_lock()
            self.phase = "combat"

        self._run_step(_body)

    def _phase_p1(self) -> None:
        if not self._in_p1() and self._in_p2():
            return

        self.action.attack()

        if self.action.check_Skill_energy_bar():
            self.phase = "p1_ult"
            return

        if self.action.check_status(_CORE_PASSIVE_NODE):

            def _body() -> None:
                self.action.logger.info("极锋: p1 核心被动，消 1 号球进 p2")
                self.action.ball_elimination_target(_P1_TO_P2_BALL)

            self._run_step(_body)
            return

        if self.action.check_status(_P1_CORE_BAR_NODE):
            self._p1_core_long_press()
            return

        self.action.attack()
        if self.action.count_signal_balls() >= _P1_BALL_MIN:
            self._p1_clear_until_core_bar()
            return

        self._run_step(lambda: self._attack_burst())

    def _phase_p1_ult(self) -> None:
        if self._in_p2():
            self.phase = "combat"
            return
        self._finish_ult_and_switch(stage="p1")

    def _phase_p2(self) -> None:
        if self.action.check_Skill_energy_bar():
            self.phase = "p2_ult"
            return

        if self.action.check_status(_P2_CORE_BAR_NODE):

            def _body() -> None:
                self.action.logger.info("极锋: p2 核心条满，消 3 号球×2 + 长按攻击")
                for _ in range(_P2_CORE_BALL_CLEAR_COUNT):
                    self.action.ball_elimination_target(_P2_CORE_BALL)
                self.action.long_press_attack(_P2_CORE_LONG_PRESS_MS)

            self._run_step(_body)
            return

        def _fallback() -> None:
            self.action.logger.info("极锋: p2 兜底，消 1 号球 + 普攻")
            self.action.ball_elimination_target(_P2_TO_P1_BALL)
            self._attack_burst(_FOLLOW_ATTACK_BURST)

        self._run_step(_fallback)

    def _phase_p2_ult(self) -> None:
        if not self._in_p2():
            self.phase = "combat"
            return
        self._finish_ult_and_switch(stage="p2")

    def on_switch_failed(self) -> None:
        self.phase = "combat"
