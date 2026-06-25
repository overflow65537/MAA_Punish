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

"""深谣战斗程序

消球规则：日常只消 2 号球；1 号为特殊球，仅在核心被动时消。
球数 OCR 从 1 号特殊球起算（1 号常驻计数，count>1 才有可消普通球）。

状态机::

    idle ──p1──► p1 ──大招条──► ult（连放至能量空）──► p1
      └──p2──► p2 ──大招条──► ult ──► switch
"""

from __future__ import annotations

from action.combat.core.role import BaseRole

_P1_PHASE = "检查阶段p1_深谣"
_P2_PHASE = "检查阶段p2_深谣"
_CORE1_NODE = "检查核心被动1_深谣"
_CORE2_NODE = "检查核心被动2_深谣"
_NORMAL_BALL = 2  # 日常消球
_CORE_BALL = 1  # 核心被动消球
_P1_CORE_DODGE_DELAY = 0.5  # 消特殊球后持续普攻再闪避（秒）
_P2_CORE_ATTACK_DURATION = 1.0  # p2 消特殊球后持续普攻再长按（秒）
_P2_CORE_LONG_PRESS_MS = 1000  # p2 核心被动长按攻击（毫秒）


class LostLullaby(BaseRole):
    """深谣：p1/p2 日常消 2 号球，核心被动消 1 号球。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ult_p2 = False

    def reset_state(self) -> None:
        super().reset_state()
        self._ult_p2 = False

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "p1":
            self._phase_p1()
        elif self.phase == "p2":
            self._phase_p2()
        elif self.phase == "ult":
            self._phase_ult()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _in_p1(self) -> bool:
        return bool(self.action.check_status(_P1_PHASE))

    def _in_p2(self) -> bool:
        return bool(self.action.check_status(_P2_PHASE))

    def _has_core_passive(self) -> bool:
        return bool(
            self.action.check_status(_CORE1_NODE)
            or self.action.check_status(_CORE2_NODE)
        )

    def _has_clearable_balls(self) -> bool:
        """深谣球数含常驻 1 号特殊球，>1 才有可消的普通球。"""
        return self.action.count_signal_balls() > 1

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        if self._in_p1():
            self.action.logger.debug("深谣: p1")
            self.phase = "p1"
            return

        if self._in_p2():
            self.action.logger.debug("深谣: p2")
            self.phase = "p2"

    def _phase_p1(self) -> None:
        """p1 优先级：大招 > 核心被动(消1号球+闪避) > 消2号球 > 普攻。"""
        if not self._in_p1():
            self.phase = "idle"
            return

        if self.action.check_Skill_energy_bar():
            self._ult_p2 = False
            self.phase = "ult"
            return

        if self._has_core_passive():
            self.action.logger.info("深谣: p1 核心被动")
            self.action.ball_elimination_target(_CORE_BALL)
            self.action.sleep_with_attack(_P1_CORE_DODGE_DELAY)
            self.action.dodge()
            return

        if self._has_clearable_balls():
            self.action.ball_elimination_target(_NORMAL_BALL)
            return

        self.action.attack()

    def _phase_p2(self) -> None:
        """p2 优先级：核心被动(消1号球+1s持续普攻+长按) > 大招 > 消2号球 > 普攻。"""
        if not self._in_p2():
            self.phase = "idle"
            return

        if self._has_core_passive():
            self.action.logger.info("深谣: p2 核心被动")
            self.action.ball_elimination_target(_CORE_BALL)
            self.action.sleep_with_attack(_P2_CORE_ATTACK_DURATION)
            self.action.long_press_attack(_P2_CORE_LONG_PRESS_MS)
            return

        if self.action.check_Skill_energy_bar():
            self._ult_p2 = True
            self.phase = "ult"
            return

        if self._has_clearable_balls():
            self.action.ball_elimination_target(_NORMAL_BALL)
            return

        self.action.attack()

    def _phase_ult(self) -> None:
        """大招连放：能量条满则继续放大，看不到满条后 p1 继续 / p2 换人。"""
        if self._ult_p2:
            if not self._in_p2():
                self.phase = "idle"
                return
        elif not self._in_p1():
            self.phase = "idle"
            return

        self.action.use_skill_until_empty()
        self.action.auxiliary_machine()
        self.action.logger.info("深谣: 大招结束")
        self.phase = "switch" if self._ult_p2 else "p1"
