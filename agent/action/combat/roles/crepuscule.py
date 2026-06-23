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

"""晖暮战斗程序

状态机::

    idle ──大招条──► ult ──► switch ──► idle
      ├──核心被动──► core（长按闪避）──► core_burst（长按1号球）──► idle
      ├──核心 CD──► core_wait ──► idle / farm
      └──兜底──► farm ──► idle
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_CORE_NODE = "检查核心被动_晖暮"
_FARM_BALL_TARGET = 9
_FARM_MAX = 100
_CORE_CD = 13
_CORE_DODGE_MS = 3000
_CORE_BALL_MS = 3500


class Crepuscule(BaseRole):
    """晖暮：一段大 + 一级 QTE 切人，核心被动长按闪避 + 消球。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._farm_ticks = 0
        self._last_core_at = 0.0

    def reset_state(self) -> None:
        super().reset_state()
        self._farm_ticks = 0
        self._last_core_at = 0.0

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "ult":
            self._phase_ult()
        elif self.phase == "core":
            self._phase_core()
        elif self.phase == "core_burst":
            self._phase_core_burst()
        elif self.phase == "core_wait":
            self._phase_core_wait()
        elif self.phase == "farm":
            self._phase_farm()
        elif self.phase == "switch":
            self._phase_switch()
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
        self.action.logger.info("晖暮: 开启核心被动")
        self.phase = "core"
        return True

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        if self.action.check_Skill_energy_bar():
            self.action.logger.info("晖暮: 大招就绪")
            self.phase = "ult"
            return

        if self._try_enter_core():
            return

        self._farm_ticks = 0
        self.phase = "farm"

    def _phase_ult(self) -> None:
        self.action.use_skill()
        self.action.auxiliary_machine()
        self.action.use_qte()
        self.phase = "switch"

    def _phase_core(self) -> None:
        self.action.long_press_dodge(_CORE_DODGE_MS)
        self._last_core_at = time.monotonic()
        self.phase = "core_burst"

    def _phase_core_burst(self) -> None:
        self.combat.context.run_action(
            "长按1号球",
            pipeline_override={"长按1号球": {"duration": _CORE_BALL_MS}},
        )
        self.action.use_qte()
        self.action.auxiliary_machine()
        self.phase = "idle"

    def _phase_core_wait(self) -> None:
        """核心被动 CD 内：优先大招，否则普攻等 CD。"""
        if self.action.check_Skill_energy_bar():
            self.phase = "ult"
            return
        if self._needs_core() and not self._core_on_cooldown():
            self.action.logger.info("晖暮: 核心被动 CD 结束")
            self.phase = "core"
            return
        if not self._needs_core():
            self.phase = "idle"
            return
        self.action.attack()

    def _phase_farm(self) -> None:
        if self.action.check_Skill_energy_bar():
            self.phase = "ult"
            return
        if self._try_enter_core():
            return
        if self.action.count_signal_balls() >= _FARM_BALL_TARGET:
            self.phase = "idle"
            return
        if self._farm_ticks >= _FARM_MAX:
            self.phase = "idle"
            return
        self.action.attack()
        self._farm_ticks += 1

    def _phase_switch(self) -> None:
        if self.switch_next():
            self.action.logger.info("晖暮: 切换完成")
        self.phase = "idle"
