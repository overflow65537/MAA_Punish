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

    idle ──► fight ──► finish ──► switch
"""

from __future__ import annotations

from action.combat.core.role import BaseRole

_FIGHT_TICKS = 10


class GeneralFight(BaseRole):
    """通用兜底：固定轮次攻击/消球/技能后 QTE 切人。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fight_ticks = 0

    def reset_state(self) -> None:
        super().reset_state()
        self._fight_ticks = 0

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "fight":
            self._phase_fight()
        elif self.phase == "finish":
            self._phase_finish()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _phase_idle(self) -> None:
        self.action.logger.info("通用战斗: 开始")
        self.action.lens_lock()
        self.action.attack()
        self._fight_ticks = 0
        self.phase = "fight"

    def _phase_fight(self) -> None:
        if self._fight_ticks >= _FIGHT_TICKS:
            self.action.attack()
            self.phase = "finish"
            return

        self.action.attack()
        self.action.ball_elimination_target()
        self.action.use_skill()
        self.action.auxiliary_machine()
        self._fight_ticks += 1

    def _phase_finish(self) -> None:
        self.action.use_qte()
        self.phase = "switch"
