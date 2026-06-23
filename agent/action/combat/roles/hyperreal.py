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

"""超刻战斗程序

状态机::

    idle ──大招条──► ult ──► idle
      ├──核心就绪──► core_open ──► core_burst ──► switch
      ├──核心 CD──► core_wait ──► idle / farm
      └──兜底──► farm ──► idle
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_CORE_NODE = "检查核心技能_超刻"
_CORE_END_NODE = "检查核心技能结束_超刻"
_CORE_BURST_MAX = 100
_CORE_TIMEOUT = 10.0
_FARM_BALL_MIN = 9
_FARM_ATTACK_BURST = 5
_FARM_ATTACK_INTERVAL_MS = 100
_CORE_CD = 13


class Hyperreal(BaseRole):
    """超刻：大招、核心长按消球、farm 攒条。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._core_ticks = 0
        self._core_deadline = 0.0
        self._last_core_at = 0.0

    def reset_state(self) -> None:
        super().reset_state()
        self._core_ticks = 0
        self._core_deadline = 0.0
        self._last_core_at = 0.0

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "ult":
            self._phase_ult()
        elif self.phase == "core_open":
            self._phase_core_open()
        elif self.phase == "core_burst":
            self._phase_core_burst()
        elif self.phase == "core_wait":
            self._phase_core_wait()
        elif self.phase == "farm":
            self._phase_farm()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _needs_core(self) -> bool:
        return bool(self.action.check_status(_CORE_NODE))

    def _core_on_cooldown(self) -> bool:
        if self._last_core_at <= 0:
            return False
        return time.monotonic() - self._last_core_at < _CORE_CD

    def _try_enter_core(self) -> bool:
        if not self._needs_core():
            return False
        if self._core_on_cooldown():
            self.phase = "core_wait"
            return True
        self.action.logger.info("超刻: 核心技能就绪")
        self.phase = "core_open"
        return True

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        if self.action.check_Skill_energy_bar():
            self.action.logger.info("超刻: 大招就绪")
            self.phase = "ult"
            return

        if self._try_enter_core():
            return

        self.phase = "farm"

    def _phase_ult(self) -> None:
        self.action.use_skill_until_empty()
        self.action.auxiliary_machine()
        self.action.use_qte()
        self.phase = "idle"

    def _phase_core_open(self) -> None:
        self.action.long_press_attack()
        self._last_core_at = time.monotonic()
        self.action.use_qte()
        self.action.auxiliary_machine()
        self._core_ticks = 0
        self._core_deadline = time.monotonic() + _CORE_TIMEOUT
        self.phase = "core_burst"

    def _phase_core_burst(self) -> None:
        if (
            self.action.check_status(_CORE_END_NODE)
            or time.monotonic() >= self._core_deadline
            or self._core_ticks >= _CORE_BURST_MAX
        ):
            self.action.logger.info("超刻: 核心技能结束")
            self.action.auxiliary_machine()
            self.phase = "switch"
            return

        if self.action.count_signal_balls():
            self.action.ball_elimination_target(1)
        self.action.use_qte()
        self.action.attack()
        self._core_ticks += 1

    def _phase_core_wait(self) -> None:
        """核心被动 CD 内：优先大招，否则普攻等 CD。"""
        if self.action.check_Skill_energy_bar():
            self.phase = "ult"
            return
        if self._needs_core() and not self._core_on_cooldown():
            self.action.logger.info("超刻: 核心被动 CD 结束")
            self.phase = "core_open"
            return
        if not self._needs_core():
            self.phase = "farm"
            return
        self.action.continuous_attack(_FARM_ATTACK_BURST, _FARM_ATTACK_INTERVAL_MS)

    def _phase_farm(self) -> None:
        if self.action.check_Skill_energy_bar():
            self.phase = "ult"
            return
        if self._try_enter_core():
            return

        self.action.continuous_attack(_FARM_ATTACK_BURST, _FARM_ATTACK_INTERVAL_MS)
        target = self.action.Arrange_Signal_Balls("any")
        if self.action.count_signal_balls() >= _FARM_BALL_MIN or target > 0:
            self.action.ball_elimination_target(target)
        self.action.attack()
        self.phase = "idle"
