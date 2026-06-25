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

"""灼惘战斗程序

状态机::

    idle ──► p1 ──大招条──► p1_ult（确认释放 → QTE）──► p2
              ├──球≥3──► 消球一次 ──► p1
              └──兜底──► 一段连续普攻 ──► p1

    p2 ──球≥3──► 消球一次 ──► p2
       ├──核心被动（球数已读且<3）──► 按住普攻（≤5s，满大则放大）──► p2_ult（确认释放 → QTE → 切人）
       └──兜底──► 普攻 ──► p2

进 p2：p1 大招 + QTE。出 p2：仅 p2 大招 + QTE + 切人。
核心被动识别节点 ``检查核心被动_灼惘`` 由低代码 Pipeline 配置（Geiravor.jsonc）。
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_CORE_PASSIVE_NODE = "检查核心被动_灼惘"
_P2_NODE = "检查阶段p2_灼惘"
_BALL_CLEAR_MIN = 3
_P1_ATTACK_BURST = 5
_P1_ATTACK_INTERVAL_MS = 50
_P2_HOLD_MAX_S = 5.0
_P2_HOLD_POLL_S = 0.05


class Geiravor(BaseRole):
    """灼惘：p1 攒大进 p2；p2 核心被动长按普攻攒大后切人。"""

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "p1":
            self._phase_p1()
        elif self.phase == "p1_ult":
            self._phase_p1_ult()
        elif self.phase == "p2":
            self._phase_p2()
        elif self.phase == "p2_ult":
            self._phase_p2_ult()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _has_core_passive(self) -> bool:
        return bool(self.action.check_status(_CORE_PASSIVE_NODE))

    def _in_p2(self) -> bool:
        return bool(self.action.check_status(_P2_NODE))

    def _enter_p2(self) -> None:
        self.action.logger.info("灼惘: 二阶段")
        self.phase = "p2"

    def _clear_one_ball(self) -> None:
        """消球一次（无颜色球，消 1 号位）。"""
        self.action.ball_elimination_target(1)

    def _hold_attack_until_skill_or_timeout(self) -> bool:
        """按住普攻并轮询大招条，最多 5 秒。返回 True 表示能量已满。"""
        self.action.down_attack()
        try:
            deadline = time.monotonic() + _P2_HOLD_MAX_S
            while time.monotonic() < deadline:
                if self.combat.context.tasker.stopping:
                    return False
                if self.action.check_Skill_energy_bar():
                    return True
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                time.sleep(min(_P2_HOLD_POLL_S, remaining))
            return False
        finally:
            self.action.up_attack()

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.phase = "p1"

    def _phase_p1(self) -> None:
        """p1：大招 > 消球 > 一段连续普攻。"""
        if self._in_p2():
            self._enter_p2()
            return

        if self.action.check_Skill_energy_bar():
            self.phase = "p1_ult"
            return

        if self.action.count_signal_balls() >= _BALL_CLEAR_MIN:
            self.action.logger.info("灼惘: p1 消球")
            self._clear_one_ball()
            return

        self.action.continuous_attack(_P1_ATTACK_BURST, _P1_ATTACK_INTERVAL_MS)

    def _phase_p1_ult(self) -> None:
        """p1 大招 → 确认能量空 → QTE → 进入 p2。"""
        self.action.logger.info("灼惘: p1 大招")
        if not self.action.use_skill_until_empty():
            self.action.logger.warning("灼惘: p1 大招未确认释放")
            self.phase = "p1"
            return

        self.action.auxiliary_machine()
        self.action.use_qte()
        self._enter_p2()

    def _phase_p2(self) -> None:
        """p2：消球 > 核心被动（球数已读且<3）> 普攻。"""
        ball_count = self.action.count_signal_balls()
        if ball_count >= _BALL_CLEAR_MIN:
            self.action.logger.info("灼惘: p2 消球")
            self._clear_one_ball()
            return

        # 球数 OCR 未命中时不判核心被动，避免进 p2 动画期间误判
        if ball_count > 0 and self._has_core_passive():
            self.action.logger.info("灼惘: p2 核心被动，按住普攻")
            if self._hold_attack_until_skill_or_timeout():
                self.phase = "p2_ult"
            return

        self.action.attack()

    def _phase_p2_ult(self) -> None:
        """p2 大招 → 确认能量空 → 立刻 QTE → 同 tick 切人（唯一出 p2 路径）。"""
        self.action.logger.info("灼惘: p2 大招")
        if not self.action.use_skill_until_empty():
            self.action.logger.warning("灼惘: p2 大招未确认释放")
            self.phase = "p2"
            return

        self.action.logger.info("灼惘: p2 大招结束，QTE 切人")
        self.action.auxiliary_machine()
        self.action.use_qte()
        self.combat.request_role_switch(self)

    def on_switch_failed(self) -> None:
        """切人失败时回到 p2，便于下轮继续。"""
        self.phase = "p2"
