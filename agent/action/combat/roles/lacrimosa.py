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

"""安魂战斗程序

双状态（常规 / 核心）::

    idle ──► 常规或核心分流
      [常规] 最高优先检查大招常规_安魂（大招1）──► ult
      [常规] 球>9 且核心被动冷却完毕 ──► enter_core
            长闪 1000ms → 0.1s → 消2 → 0.1s → 消1 → 等核心（普攻+消1，≤3s，超时回常规重试）
      [常规] 兜底 ──► 普攻

      [核心] 最优先检查大招核心_安魂（大招2）
            见大招 ──► 只消 2 号球直到球≤1 ──► core_ult（持续点大招，等到回常规）
            未见大招 ──► 有球则消 2，否则普攻

Pipeline：Check_Characters_Skill/Lacrimosa.jsonc
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_NORMAL_NODE = "检查常规状态_安魂"
_CORE_NODE = "检查核心状态_安魂"
_CORE_READY_NODE = "检查核心被动冷却_安魂"
_ULT_NORMAL_NODE = "检查大招常规_安魂"  # 大招1：仅常规态
_ULT_CORE_NODE = "检查大招核心_安魂"  # 大招2：仅核心态

_ENTER_BALL_MIN = 9  # 球数须严格大于该值
_CORE_ULT_BALL_MAX = 1  # 见大招后球≤该值即可开始连放大招
_DODGE_HOLD_MS = 1000
_ENTER_GAP_S = 0.1  # 长闪/消球之间的间隔（文案 0.1ms，按 0.1s）
_ENTER_CORE_WAIT_S = 3.0
_ENTER_CORE_POLL_S = 0.05
_BALL_SLOT_1 = 1
_BALL_SLOT_2 = 2
_ULT_TIMEOUT_S = 15.0
_ULT_POLL_S = 0.05


class Lacrimosa(BaseRole):
    """安魂：常规放大切人 / 攒球进核心；核心见大招后消球再连放大回常规。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._core_ult_latched = False

    def reset_state(self) -> None:
        super().reset_state()
        self._core_ult_latched = False

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "ult":
            self._phase_ult()
        elif self.phase == "enter_core":
            self._phase_enter_core()
        elif self.phase == "core_ult":
            self._phase_core_ult()
        elif self.phase == "core":
            self._phase_core()
        elif self.phase == "normal":
            self._phase_normal()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _in_normal(self) -> bool:
        return bool(self.action.check_status(_NORMAL_NODE))

    def _in_core(self) -> bool:
        return bool(self.action.check_status(_CORE_NODE))

    def _core_ready(self) -> bool:
        return bool(self.action.check_status(_CORE_READY_NODE))

    def _ult_ready_normal(self) -> bool:
        return bool(self.action.check_status(_ULT_NORMAL_NODE))

    def _ult_ready_core(self) -> bool:
        return bool(self.action.check_status(_ULT_CORE_NODE))

    def _poke_before_recognize(self) -> None:
        """识别前点几下普攻，避免站桩导致模板不稳。"""
        self.action.attack()
        self.action.attack()

    def _route_by_form(self) -> str | None:
        """按识别节点分流到 normal / core；均未命中返回 None。"""
        self._poke_before_recognize()
        if self._in_core():
            return "core"
        if self._in_normal():
            return "normal"
        return None

    def _run_step(self, body) -> None:
        self.action.attack()
        try:
            body()
        finally:
            self.action.attack()

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.action.attack()
        routed = self._route_by_form()
        if routed == "core":
            self.action.logger.info("安魂: 核心状态")
            self._core_ult_latched = False
            self.phase = "core"
            return
        if routed == "normal":
            self.action.logger.info("安魂: 常规状态")
            self.phase = "normal"
            return
        self.action.logger.debug("安魂: 未识别形态，普攻等待")
        self.action.attack()

    def _phase_normal(self) -> None:
        # 最高优先：常规大招1（先识别再普攻，避免冲掉指示）
        if self._ult_ready_normal():
            self.action.logger.info("安魂: 常规大招就绪")
            self.phase = "ult"
            return

        self._poke_before_recognize()
        if self._in_core():
            self._core_ult_latched = False
            self.phase = "core"
            return
        if not self._in_normal():
            self.phase = "idle"
            return

        balls = self.action.count_signal_balls()
        if balls > _ENTER_BALL_MIN and self._core_ready():
            self.action.logger.info("安魂: 球>%d 且核心被动冷却完毕，进核心", _ENTER_BALL_MIN)
            self.phase = "enter_core"
            return

        self.action.attack()

    def _phase_ult(self) -> None:
        """常规态大招：只用大招1 节点；先按技能再识别，避免普攻把指示冲掉。"""
        self.action.logger.info("安魂: 常规态大招")
        deadline = time.monotonic() + _ULT_TIMEOUT_S
        presses = 0
        while time.monotonic() < deadline:
            if self.combat.context.tasker.stopping:
                self.phase = "normal"
                return

            # 已在 normal 确认过大招1；此处先按技能，再查是否还在
            self.action.use_skill()
            presses += 1
            self.action.attack()
            time.sleep(_ULT_POLL_S)

            if not self._ult_ready_normal():
                self.action.logger.info("安魂: 大招1 消失 presses=%d", presses)
                break
        else:
            self.action.logger.warning("安魂: 大招释放超时 %.0fs presses=%d", _ULT_TIMEOUT_S, presses)
            self.phase = "normal"
            return

        self.action.auxiliary_machine()
        self.action.use_qte()
        self.combat.request_role_switch(self)

    def _phase_enter_core(self) -> None:
        """长闪 → 消2 → 消1，再等核心态；超时回常规让状态机重试。"""
        self.action.logger.info("安魂: 进核心连段")
        self._core_ult_latched = False

        def _combo() -> None:
            self.action.long_press_dodge(_DODGE_HOLD_MS)
            time.sleep(_ENTER_GAP_S)
            self.action.ball_elimination_target(_BALL_SLOT_2)
            time.sleep(_ENTER_GAP_S)
            self.action.ball_elimination_target(_BALL_SLOT_1)

        self._run_step(_combo)

        deadline = time.monotonic() + _ENTER_CORE_WAIT_S
        while time.monotonic() < deadline:
            if self.combat.context.tasker.stopping:
                self.phase = "normal"
                return
            self.action.attack()
            self.action.ball_elimination_target(_BALL_SLOT_1)
            self._poke_before_recognize()
            if self._in_core():
                self.action.logger.info("安魂: 已进入核心状态")
                self.phase = "core"
                return
            time.sleep(_ENTER_CORE_POLL_S)

        self.action.logger.warning(
            "安魂: %.0fs 未进核心，回常规重试", _ENTER_CORE_WAIT_S
        )
        self.phase = "normal"

    def _phase_core(self) -> None:
        self._poke_before_recognize()
        if self._in_normal():
            self._core_ult_latched = False
            self.phase = "normal"
            return
        if not self._in_core():
            self.phase = "idle"
            return

        # 最优先：识别核心大招（大招2）；命中后锁存，直到回常规
        if self._ult_ready_core():
            if not self._core_ult_latched:
                self.action.logger.info("安魂: 核心见大招2，开始消2号球")
            self._core_ult_latched = True

        balls = self.action.count_signal_balls()
        if self._core_ult_latched:
            if balls > _CORE_ULT_BALL_MAX:
                self.action.ball_elimination_target(_BALL_SLOT_2)
                return
            self.action.logger.info(
                "安魂: 核心球≤%d，持续点大招等回常规", _CORE_ULT_BALL_MAX
            )
            self.phase = "core_ult"
            return

        # 未见大招：有球消2，否则普攻等待
        if balls > 0:
            self.action.ball_elimination_target(_BALL_SLOT_2)
            return
        self.action.attack()

    def _phase_core_ult(self) -> None:
        """球≤1 后持续点大招，直到回到常规。"""
        self._poke_before_recognize()
        if self._in_normal():
            self.action.logger.info("安魂: 核心大招结束，回常规")
            self._core_ult_latched = False
            self.phase = "normal"
            return

        self.action.use_skill()
        self.action.attack()

    def on_switch_failed(self) -> None:
        self._core_ult_latched = False
        self.phase = "normal"
