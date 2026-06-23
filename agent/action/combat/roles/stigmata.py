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

    idle(p1) ──► farm（持续 attack）──► ult / core / core_wait
    idle(p2) ──► farm ──► ult ──► use_qte ──► switch（CD 中回 farm 普攻）
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_P1_NODE = "检查比安卡·深痕一阶段"
_CORE_NODE = "检查核心被动_深痕"
_CORE_BURST = 10
_CORE_CD = 18  # 照域cd12秒，时滞演算1秒,照域本身4秒1秒误差


class Stigmata(BaseRole):
    """深痕：一阶段核心消球，大招就绪切人。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._core_ticks = 0
        self._last_core_at = 0.0
        self._p2 = False
        self._pending_switch = False

    def reset_state(self) -> None:
        super().reset_state()
        self._core_ticks = 0
        self._last_core_at = 0.0
        self._p2 = False
        self._pending_switch = False

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "ult":
            self._phase_ult()
        elif self.phase == "core":
            self._phase_core()
        elif self.phase == "core_wait":
            self._phase_core_wait()
        elif self.phase == "core_burst":
            self._phase_core_burst()
        elif self.phase == "farm":
            self._phase_farm()
        elif self.phase == "switch":
            self._phase_switch()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _needs_core(self) -> bool:
        return bool(
            self.action.check_status(_P1_NODE) and self.action.check_status(_CORE_NODE)
        )

    def _core_on_cooldown(self) -> bool:
        if self._last_core_at <= 0:
            return False
        return time.monotonic() - self._last_core_at < _CORE_CD

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        if self._pending_switch:
            self.phase = "switch" if self.combat.can_switch() else "farm"
            return

        if self.action.check_Skill_energy_bar():
            self.phase = "ult"
            return

        if not self._p2 and self._needs_core():
            if self._core_on_cooldown():
                self.phase = "core_wait"
                return
            self.action.logger.info("深痕: 开启照域")
            self.phase = "core"
            return

        self.phase = "farm"

    def _phase_ult(self) -> None:
        if self._p2:
            self.action.use_skill()
            self.action.auxiliary_machine()
            self.action.use_qte()
            self.action.logger.info("深痕: p2 大招后 QTE 换人")
            self._pending_switch = True
            self.phase = "switch"
            return

        self.action.use_skill()
        self.action.auxiliary_machine()
        if self.action.check_Skill_energy_bar():
            self.action.logger.info("深痕: p1 大招能量仍在，继续大招")
            return
        self.action.logger.info("深痕: p1 大招结束，QTE 进入 p2")
        self.action.use_qte()
        self._p2 = True
        self.phase = "farm"

    def _phase_core(self) -> None:
        self.action.long_press_dodge()
        self._last_core_at = time.monotonic()
        self._core_ticks = 0
        self.phase = "core_burst"

    def _phase_core_wait(self) -> None:
        """照域 CD 内：核心被动仍触发时只普攻，CD 结束再开照域。"""
        if self.action.check_Skill_energy_bar():
            self.phase = "ult"
            return
        self.action.attack()
        if not self._needs_core():
            self.phase = "farm"
            return
        if not self._core_on_cooldown():
            self.action.logger.info("深痕: 照域 CD 结束，开启照域")
            self.phase = "core"

    def _phase_core_burst(self) -> None:
        self.action.ball_elimination_target(1)
        self.action.attack()
        self._core_ticks += 1
        if self._core_ticks >= _CORE_BURST:
            self.phase = "farm"

    def _phase_farm(self) -> None:
        """持续普攻，仅在 farm 内检查大招/照域，避免反复走 idle 多重识别。"""
        if self._pending_switch:
            if self.combat.can_switch():
                self.phase = "switch"
                return
            self.action.attack()
            return

        if self.action.check_Skill_energy_bar():
            self.phase = "ult"
            return
        if not self._p2 and self._needs_core():
            if self._core_on_cooldown():
                self.phase = "core_wait"
                return
            self.action.logger.info("深痕: 开启照域")
            self.phase = "core"
            return
        self.action.attack()

    def _phase_switch(self) -> None:
        if self.switch_next():
            self.action.logger.info("深痕: 切换完成")
            self._pending_switch = False
            self.phase = "idle"
            return
        self.action.logger.info("深痕: 切人 CD 中，继续 p2 普攻")
        self.phase = "farm"
