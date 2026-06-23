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

"""深痕战斗程序

状态机::

    idle ──大招条──► ult ──► switch ──► idle
      ├──一阶段+核心被动──► core ──► core_burst ──► idle
      └──兜底──► farm ──► idle
"""

from __future__ import annotations

from action.combat.core.role import BaseRole

_P1_NODE = "检查比安卡·深痕一阶段"
_CORE_NODE = "检查核心被动_深痕"
_CORE_BURST = 10
_FARM_TICKS = 8


class Stigmata(BaseRole):
    """深痕：一阶段核心消球，大招就绪切人。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._core_ticks = 0
        self._farm_ticks = 0

    def reset_state(self) -> None:
        super().reset_state()
        self._core_ticks = 0
        self._farm_ticks = 0

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
        elif self.phase == "farm":
            self._phase_farm()
        elif self.phase == "switch":
            self._phase_switch()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        if self.action.check_Skill_energy_bar():
            self.phase = "ult"
            return

        if self.action.check_status(_P1_NODE) and self.action.check_status(_CORE_NODE):
            self.action.logger.info("深痕: 开启照域")
            self.phase = "core"
            return

        self._farm_ticks = 0
        self.phase = "farm"

    def _phase_ult(self) -> None:
        self.action.use_skill()
        self.action.auxiliary_machine()
        self.phase = "idle"  # switch

    def _phase_core(self) -> None:
        self.action.long_press_dodge()
        self._core_ticks = 0
        self.phase = "core_burst"

    def _phase_core_burst(self) -> None:
        self.action.ball_elimination_target(1)
        self.action.attack()
        self._core_ticks += 1
        if self._core_ticks >= _CORE_BURST:
            self.phase = "idle"

    def _phase_farm(self) -> None:
        self.action.attack()
        self._farm_ticks += 1
        if self._farm_ticks >= _FARM_TICKS:
            self.phase = "idle"

    def _phase_switch(self) -> None:
        # if self.switch_next():
        #     self.action.logger.info("深痕: 切换完成")
        self.phase = "idle"
