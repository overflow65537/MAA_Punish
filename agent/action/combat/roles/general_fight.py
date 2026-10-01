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

    idle ──► farm（消球2 + 攻击，直至大招条满）──► ult（技能 + 攻击 + 消球2）──► switch
              └── 长时间未出大 ──► switch
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_FARM_MAX = 100
_BALL_SLOT = 2
_ULT_POLL_INTERVAL = 0.05


class GeneralFight(BaseRole):
    """通用兜底：盲按 2 号球攒大 → 大招连段 → 切人。"""

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
        else:
            self.phase = "idle"
            self._phase_idle()

    def _phase_idle(self) -> None:
        self.action.logger.info("通用战斗: 开始")
        self.action.lens_lock()
        self.action.ball_elimination_target(_BALL_SLOT)
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

        self.action.ball_elimination_target(_BALL_SLOT)
        self.action.attack()
        self._farm_ticks += 1

    def _phase_ult(self) -> None:
        timeout = self.action.SKILL_BURST_TIMEOUT
        deadline = time.monotonic() + timeout
        presses = 0
        self.action.logger.info("通用战斗: 大招循环（技能 + 攻击 + 消球2）")

        while time.monotonic() < deadline:
            if self.combat.context.tasker.stopping:
                self.action.logger.info("通用战斗: 大招中止 presses=%d", presses)
                break
            self.action.use_skill()
            presses += 1
            if not self.action.check_Skill_energy_bar(fresh=True):
                self.action.logger.info("通用战斗: 大招结束 presses=%d", presses)
                break
            self.action.attack()
            self.action.ball_elimination_target(_BALL_SLOT)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(_ULT_POLL_INTERVAL, remaining))
        else:
            self.action.logger.warning(
                "通用战斗: 大招超时 %.0fs presses=%d", timeout, presses
            )

        self.phase = "switch"
