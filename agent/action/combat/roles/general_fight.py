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

"""通用战斗程序

状态机::

    idle ──► farm ──► switch（超时未出大，不用 QTE）
              │
              └── 大招条满 ──► ult ──► finish（QTE 一次）──► switch
"""

from __future__ import annotations

from action.combat.core.role import BaseRole

_FARM_MAX = 100


class GeneralFight(BaseRole):
    """通用兜底：攒大 → 大招 → QTE 一次 → 切人。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._farm_ticks = 0

    def reset_state(self) -> None:
        super().reset_state()
        self._farm_ticks = 0

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "farm":
            self._phase_farm()
        elif self.phase == "ult":
            self._phase_ult()
        elif self.phase == "finish":
            self._phase_finish()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _phase_idle(self) -> None:
        self.action.logger.info("通用战斗: 开始")
        self.action.lens_lock()
        self.action.attack()
        self._farm_ticks = 0
        self.phase = "farm"

    def _phase_farm(self) -> None:
        if self.action.check_Skill_energy_bar():
            self.action.logger.info("通用战斗: 大招就绪")
            self.phase = "ult"
            return

        if self._farm_ticks >= _FARM_MAX:
            self.action.logger.info("通用战斗: 未攒出大招，直接切人")
            self.phase = "switch"
            return

        self.action.attack()
        self.action.ball_elimination_target()
        self.action.auxiliary_machine()
        self._farm_ticks += 1

    def _phase_ult(self) -> None:
        self.action.use_skill_until_empty()
        self.phase = "finish"

    def _phase_finish(self) -> None:
        self.action.use_qte()
        self.phase = "switch"
