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

"""亡歌战斗程序

p1/p2 打法一致，仅按大招次数分支（两次大之间 CD 5s，第二次大后切人）::

    idle ──► combat
      大招可放 ──► ult（连按技能直至能量条消失）──► 辅助机 ──► QTE ──►（第 2 次）切人
      核心被动 ──► 消 1 号球
      球≥3 ──► 消 2 号球 ──► 25ms ──► 闪避
      兜底 ──► 普攻连段

Pipeline：Check_Characters_Skill/Dirge.jsonc
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_CORE_PASSIVE_NODE = "检查核心被动_亡歌"

_ULT_MAX = 2
_ULT_COOLDOWN_S = 5.0
_ULT_RELEASE_TIMEOUT_S = 15.0
_CORE_BALL = 1
_OVERFLOW_BALL = 2
_BALL_MIN = 3
_BALL_DODGE_GAP_S = 0.025
_ATTACK_BURST = 8
_ATTACK_INTERVAL_MS = 50


class Dirge(BaseRole):
    """亡歌：双大切人；核心被动消 1 球；满球消 2 球 + 闪避。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ult_count = 0
        self._last_ult_at = 0.0
        self._ult_releasing = False
        self._ult_release_started_at = 0.0

    def reset_state(self) -> None:
        super().reset_state()
        self._ult_count = 0
        self._last_ult_at = 0.0
        self._ult_releasing = False
        self._ult_release_started_at = 0.0

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "ult":
            self._phase_ult()
        else:
            self._phase_combat()

    def _attack_burst(self, count: int = _ATTACK_BURST) -> None:
        self.action.continuous_attack(count, _ATTACK_INTERVAL_MS)

    def _run_step(self, body) -> None:
        self.action.attack()
        try:
            body()
        finally:
            self.action.attack()

    def _can_use_ult(self) -> bool:
        if self._ult_releasing:
            return False
        if self._ult_count >= _ULT_MAX:
            return False
        if not self.action.check_Skill_energy_bar():
            return False
        if self._ult_count == 1 and (
            time.monotonic() - self._last_ult_at < _ULT_COOLDOWN_S
        ):
            return False
        return True

    def _begin_ult_release(self) -> None:
        self._ult_releasing = True
        self._ult_release_started_at = time.monotonic()
        self.action.logger.info("亡歌: 第 %d 次大招释放中", self._ult_count + 1)

    def _ult_release_timed_out(self) -> bool:
        if self._ult_release_started_at <= 0:
            return False
        return (
            time.monotonic() - self._ult_release_started_at
            >= _ULT_RELEASE_TIMEOUT_S
        )

    def _finish_ult_release(self) -> None:
        self.action.logger.info("亡歌: 大招能量条已空")
        self.action.attack()
        self.action.auxiliary_machine()
        self.action.use_qte()
        self._ult_releasing = False
        self._ult_release_started_at = 0.0
        self._ult_count += 1
        self._last_ult_at = time.monotonic()

        if self._ult_count >= _ULT_MAX:
            self.action.logger.info("亡歌: 第二次大招结束，切人")
            self.combat.request_role_switch(self)
        else:
            self.action.logger.info(
                "亡歌: 第一次大招结束，等待 %gs CD", _ULT_COOLDOWN_S
            )
            self.phase = "combat"

    def _phase_idle(self) -> None:
        def _body() -> None:
            self.action.lens_lock()
            self.phase = "combat"

        self._run_step(_body)

    def _phase_ult(self) -> None:
        if not self._ult_releasing:
            self._begin_ult_release()

        if self.action.check_Skill_energy_bar():
            if self._ult_release_timed_out():
                self.action.logger.warning(
                    "亡歌: 大招释放超时 %.0fs", _ULT_RELEASE_TIMEOUT_S
                )
                self._ult_releasing = False
                self._ult_release_started_at = 0.0
                self.phase = "combat"
                return

            self.action.use_skill()
            self.action.attack()
            return

        if not self._ult_releasing:
            self.phase = "combat"
            return

        self._finish_ult_release()

    def _phase_combat(self) -> None:
        self.action.attack()

        if self._can_use_ult():
            self.phase = "ult"
            return

        if self.action.check_status(_CORE_PASSIVE_NODE):

            def _body() -> None:
                self.action.logger.info("亡歌: 核心被动，消 1 号球")
                self.action.ball_elimination_target(_CORE_BALL)

            self._run_step(_body)
            return

        self.action.attack()
        if self.action.count_signal_balls() >= _BALL_MIN:

            def _body() -> None:
                self.action.logger.info("亡歌: 球≥3，消 2 号球 + 闪避")
                self.action.ball_elimination_target(_OVERFLOW_BALL)
                time.sleep(_BALL_DODGE_GAP_S)
                self.action.dodge()

            self._run_step(_body)
            return

        self._run_step(lambda: self._attack_burst())

    def on_switch_failed(self) -> None:
        self.phase = "combat"
