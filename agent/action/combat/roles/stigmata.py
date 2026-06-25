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

    idle ──► p1（优先：放大 > 照域 > 照域后消球）──► ult（p1 连放）
      └──► p2（持续普攻攒大）──► ult ──► use_qte ──► switch
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_P1_NODE = "检查比安卡·深痕一阶段"
_P2_NODE = "检查比安卡·深痕二阶段"
_CORE_NODE = "检查核心被动_深痕"
_CORE_BURST = 10
_CORE_CD = 18  # 照域cd12秒，时滞演算1秒,照域本身4秒1秒误差


class Stigmata(BaseRole):
    """深痕：一阶段照域消球，二阶段持续攻击，有大则放。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._core_ticks = 0
        self._last_core_at = 0.0
        self._pending_switch = False
        self._last_log_key = ""

    def reset_state(self) -> None:
        super().reset_state()
        self._core_ticks = 0
        self._last_core_at = 0.0
        self._pending_switch = False
        self._last_log_key = ""

    def on_switch_succeeded(self) -> None:
        self._pending_switch = False

    def on_switch_failed(self) -> None:
        self.phase = "p2"

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
        elif self.phase == "core":
            self._phase_core()
        elif self.phase == "core_wait":
            self._phase_core_wait()
        elif self.phase == "core_burst":
            self._phase_core_burst()
        else:
            self.phase = "idle"
            self._phase_idle()
        self._log_state()

    def _recognition_stage(self) -> str:
        if self._in_p2():
            return "p2"
        if self._in_p1():
            return "p1"
        return "unknown"

    def _log_state(self, *, note: str = "") -> None:
        stage = self._recognition_stage()
        key = f"{stage}|{self.phase}|{note}"
        if key == self._last_log_key:
            return
        self._last_log_key = key
        msg = f"深痕: 阶段={stage} 状态={self.phase}"
        if note:
            msg += f" ({note})"
        self.action.logger.info(msg)

    def _in_p1(self) -> bool:
        return bool(self.action.check_status(_P1_NODE))

    def _in_p2(self) -> bool:
        return bool(self.action.check_status(_P2_NODE))

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
            self.phase = "switch" if self.combat.can_switch() else "p2"
            return

        if self._in_p2():
            self.phase = "p2"
            return
        if self._in_p1():
            self.phase = "p1"
            return
        self.action.attack()

    def _phase_p1(self) -> None:
        """一阶段：放大 > 照域 > 照域后消球（core_burst），否则普攻等核心被动。"""
        if self._in_p2():
            self.phase = "p2"
            return
        if not self._in_p1():
            self.phase = "idle"
            return

        if self.action.check_Skill_energy_bar():
            self.phase = "ult"
            return

        if self._needs_core() and not self._core_on_cooldown():
            self.action.logger.info("深痕: 开启照域")
            self.phase = "core"
            return

        if self._needs_core() and self._core_on_cooldown():
            self.phase = "core_wait"
            return

        self.action.attack()

    def _phase_p2(self) -> None:
        """二阶段：持续普攻，有大则放大后换人。"""
        if self._in_p1() and not self._in_p2():
            self.phase = "p1"
            return
        if not self._in_p2():
            self.phase = "idle"
            return

        if self._pending_switch:
            if self.combat.can_switch():
                self.phase = "switch"
                return
            self.action.attack()
            return

        if self.action.check_Skill_energy_bar():
            self.phase = "ult"
            return

        self.action.attack()

    def _phase_ult(self) -> None:
        if self._in_p2():
            self.action.use_skill_until_empty()
            self.action.auxiliary_machine()
            self.action.use_qte()
            self.action.logger.info("深痕: p2 大招后 QTE 换人")
            self._pending_switch = True
            self.phase = "switch"
            return

        self.action.use_skill_until_empty()
        self.action.auxiliary_machine()
        self.action.logger.info("深痕: p1 大招结束")
        self.phase = "p2" if self._in_p2() else "p1"

    def _phase_core(self) -> None:
        self.action.long_press_dodge()
        self._last_core_at = time.monotonic()
        self._core_ticks = 0
        self.phase = "core_burst"

    def _phase_core_wait(self) -> None:
        """照域 CD 内：优先放大，否则普攻等 CD。"""
        if self._in_p2():
            self.phase = "p2"
            return
        if self.action.check_Skill_energy_bar():
            self.phase = "ult"
            return
        if self._needs_core() and not self._core_on_cooldown():
            self.action.logger.info("深痕: 照域 CD 结束，开启照域")
            self.phase = "core"
            return
        if not self._needs_core():
            self.phase = "p1"
            return
        self.action.attack()

    def _phase_core_burst(self) -> None:
        """照域后消球：有大优先放大，否则只消球。"""
        if self._in_p2():
            self.phase = "p2"
            return
        if self.action.check_Skill_energy_bar():
            self.phase = "ult"
            return
        self.action.ball_elimination_target(1)
        self._core_ticks += 1
        if self._core_ticks >= _CORE_BURST:
            self.phase = "p2" if self._in_p2() else "p1"
