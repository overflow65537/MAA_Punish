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

"""霁梦战斗程序

状态机::

    idle ──普攻1+核心条──► p1_core ──► p1_burst(普攻1在则 skill) ──► p1_post_ult(8s 点2号球)
      ├──p1_post_ult 超时──► idle
      ├──p1_post_ult 识别普攻2──► p2 分支
      ├──普攻1消球──► p1_clear ──► idle
      ├──普攻2──► p2_farm（持续普攻，有球消球）──► p2_core_wait ──► p2_finish ──► p2_burst ──► use_qte ──► switch
      └──兜底──► farm ──► idle
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_ATK1_NODE = "检查普攻1_霁梦"
_CORE_BAR_NODE = "检查核心条_霁梦"
_ATK2_NODE = "检查普攻2_霁梦"
_CORE_BALL_NODE = "检查核心球_霁梦"
_CORE_BAR2_NODE = "检查核心条2_霁梦"
_P1_BALL_MIN = 5
_P1_BURST_TICKS = 15
_P1_POST_ULT_DURATION = 8.0
_P2_BURST_TICKS = 15
_P2_CORE_WAIT_TIMEOUT = 5.0
_FARM_MAX = 30


class Limpidity(BaseRole):
    """霁梦：普攻1/2 分流，核心条/核心球触发连段。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._burst_ticks = 0
        self._burst_total = 0
        self._farm_ticks = 0
        self._p2_core_deadline = 0.0
        self._p1_post_ult_deadline = 0.0

    def reset_state(self) -> None:
        super().reset_state()
        self._burst_ticks = 0
        self._burst_total = 0
        self._farm_ticks = 0
        self._p2_core_deadline = 0.0
        self._p1_post_ult_deadline = 0.0

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "p1_clear":
            self._phase_p1_clear()
        elif self.phase == "p1_core":
            self._phase_p1_core()
        elif self.phase == "p1_burst":
            self._phase_p1_burst()
        elif self.phase == "p1_post_ult":
            self._phase_p1_post_ult()
        elif self.phase == "p2_farm":
            self._phase_p2_farm()
        elif self.phase == "p2_core_wait":
            self._phase_p2_core_wait()
        elif self.phase == "p2_finish":
            self._phase_p2_finish()
        elif self.phase == "p2_burst":
            self._phase_p2_burst()
        elif self.phase == "farm":
            self._phase_farm()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _is_atk1(self) -> bool:
        return bool(self.action.check_status(_ATK1_NODE))

    def _is_atk2(self) -> bool:
        return bool(self.action.check_status(_ATK2_NODE))

    def _begin_burst(self, total: int, next_phase: str) -> None:
        self._burst_total = total
        self._burst_ticks = 0
        self.phase = next_phase

    def _enter_p2(self) -> None:
        if self.action.check_status(_CORE_BALL_NODE):
            self.action.logger.info("霁梦: 见证我的意志")
            self._p2_core_deadline = time.monotonic() + _P2_CORE_WAIT_TIMEOUT
            self.phase = "p2_core_wait"
            return
        self.phase = "p2_farm"

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        if self._is_atk1():
            if self.action.check_status(_CORE_BAR_NODE):
                self.action.logger.info("霁梦: 直面天闪")
                self.phase = "p1_core"
                return
            target = self.action.Arrange_Signal_Balls()
            if target > 0 or self.action.count_signal_balls() >= _P1_BALL_MIN:
                self.phase = "p1_clear"
                return

        if self._is_atk2():
            self._enter_p2()
            return

        self._farm_ticks = 0
        self.phase = "farm"

    def _phase_p1_clear(self) -> None:
        target = self.action.Arrange_Signal_Balls()
        self.action.ball_elimination_target(target)
        self.action.attack()
        self.phase = "idle"

    def _enter_p1_post_ult(self, *, reason: str = "") -> None:
        if reason:
            self.action.logger.info(reason)
        self.action.logger.info("霁梦: p1 大招结束，点2号球")
        self.action.auxiliary_machine()
        self.action.use_qte()
        if self._is_atk2():
            self.action.logger.info("霁梦: p1 大招后识别到普攻2")
            self._enter_p2()
        elif time.monotonic() < self._p1_post_ult_deadline:
            self.phase = "p1_post_ult"
        else:
            self.phase = "idle"

    def _phase_p1_core(self) -> None:
        self.action.long_press_dodge(1000)
        self.action.logger.info("霁梦: 以苦厄澈我心镜")
        self._p1_post_ult_deadline = time.monotonic() + _P1_POST_ULT_DURATION
        if not self._is_atk1():
            self._enter_p1_post_ult(reason="霁梦: 未识别普攻1，跳过 p1 大招连段")
            return
        self._begin_burst(_P1_BURST_TICKS, "p1_burst")

    def _phase_p1_burst(self) -> None:
        if not self._is_atk1():
            self._enter_p1_post_ult(reason="霁梦: 未识别普攻1，跳过 p1 大招连段")
            return
        self.action.use_skill_until_empty()
        self.action.auxiliary_machine()
        self.action.attack()
        self._enter_p1_post_ult()

    def _phase_p1_post_ult(self) -> None:
        """p1 大招后 8s 内点 2 号球；识别普攻2 走 p2，超时回 idle。"""
        self.action.ball_elimination_target(2)
        if self._is_atk2():
            self.action.logger.info("霁梦: p1 大招后识别到普攻2")
            self._enter_p2()
            return
        if time.monotonic() >= self._p1_post_ult_deadline:
            self.action.logger.info("霁梦: p1 大招后点2号球超时")
            self.phase = "idle"

    def _phase_p2_farm(self) -> None:
        """p2 攒条：每 tick 普攻，有球则消球；不再走 idle 的多重识别。"""
        if not self._is_atk2():
            self.phase = "idle"
            return
        if self.action.check_status(_CORE_BALL_NODE):
            self.action.logger.info("霁梦: 见证我的意志")
            self._p2_core_deadline = time.monotonic() + _P2_CORE_WAIT_TIMEOUT
            self.phase = "p2_core_wait"
            return
        if self.action.count_signal_balls() > 0:
            self.action.ball_elimination_target()
        self.action.attack()

    def _phase_p2_core_wait(self) -> None:
        if self.action.check_status(_CORE_BAR2_NODE):
            self.phase = "p2_finish"
            return
        if time.monotonic() >= self._p2_core_deadline:
            self.action.logger.warning("霁梦: 等待核心条2超时")
            self.phase = "p2_farm" if self._is_atk2() else "idle"
            return
        self.action.ball_elimination_target(1)
        self.action.attack()

    def _phase_p2_finish(self) -> None:
        self.action.long_press_attack(3000)
        self.action.logger.info("霁梦: 终于梦醒时分")
        self._begin_burst(_P2_BURST_TICKS, "p2_burst")

    def _phase_p2_burst(self) -> None:
        self.action.use_skill_until_empty()
        self.action.auxiliary_machine()
        self.action.logger.info("霁梦: 映天地渡你新生")
        self.action.use_qte()
        self.phase = "switch"

    def _phase_farm(self) -> None:
        self.action.attack()
        self._farm_ticks += 1
        if self._farm_ticks >= _FARM_MAX:
            self.phase = "idle"
