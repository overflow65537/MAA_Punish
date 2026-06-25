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

"""骇影战斗程序

状态机::

    idle ──二阶段──► p2_scan ⇄ p2_red / p2_yellow / p2_blue ──► p2_ult ──► switch
      ├──球≥9──► p1_clear ──► p1_ult ──► idle
      └──兜底──► p1_farm ──► idle

二阶段按 UI 红/黄/蓝球识别驱动（Spectre.jsonc）::

    红球命中: 消2号×4 → 回到 p2_scan
    黄球命中: 普攻×3 + 消1号，循环2次 → 回到 p2_scan
    蓝球命中: 长按攻击 700ms → 消1号 → 回到 p2_scan
    RGB 均未命中（仍在二阶段）: p2_ult 放大招
    大招后: 骇影普通消失 → QTE → switch
    离开二阶段: switch
"""

from __future__ import annotations

from action.combat.core.role import BaseRole

_P2_NODE = "检查骇影2阶段"
_P2_RED_NODE = "骇影二阶段红球"
_P2_YELLOW_NODE = "骇影二阶段黄球"
_P2_BLUE_NODE = "骇影二阶段蓝球"
_P2_NORMAL_NODE = "骇影普通"
_P1_CLEAR_BALL_MIN = 9
_P1_LOOP_MAX = 100
_P1_ATTACK_BURST = 5
_P1_ATTACK_INTERVAL_MS = 50
_P2_YELLOW_LOOPS = 2
_P2_YELLOW_ATTACK_COUNT = 3
_P2_YELLOW_ATTACK_INTERVAL_MS = 50
_P2_BLUE_LONG_PRESS_MS = 700
_P2_ULT_WAIT_MAX = 100


class Spectre(BaseRole):
    """骇影：一阶段攒大进二阶段；二阶段按 UI 球色识别连段后切人。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._p1_ticks = 0
        self._p2_blue_step = 0
        self._p2_ult_fired = False
        self._p2_ult_wait_ticks = 0

    def reset_state(self) -> None:
        super().reset_state()
        self._p1_ticks = 0
        self._p2_blue_step = 0
        self._p2_ult_fired = False
        self._p2_ult_wait_ticks = 0

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "p1_farm":
            self._phase_p1_farm()
        elif self.phase == "p1_clear":
            self._phase_p1_clear()
        elif self.phase == "p1_ult":
            self._phase_p1_ult()
        elif self.phase == "p2_scan":
            self._phase_p2_scan()
        elif self.phase == "p2_red":
            self._phase_p2_red()
        elif self.phase == "p2_yellow":
            self._phase_p2_yellow()
        elif self.phase == "p2_blue":
            self._phase_p2_blue()
        elif self.phase == "p2_ult":
            self._phase_p2_ult()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _in_p2(self) -> bool:
        return bool(self.action.check_status(_P2_NODE))

    def _p2_ball_active(self, node: str) -> bool:
        return bool(self.action.check_status(node))

    def _finish_p2(self) -> None:
        self.action.auxiliary_machine()
        self._p2_blue_step = 0
        self._p2_ult_fired = False
        self._p2_ult_wait_ticks = 0
        self.phase = "switch"

    def _enter_p2(self) -> None:
        self.action.logger.info("骇影: 二阶段")
        self._p2_blue_step = 0
        self._p2_ult_fired = False
        self._p2_ult_wait_ticks = 0
        self.phase = "p2_scan"

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.action.continuous_attack(_P1_ATTACK_BURST, _P1_ATTACK_INTERVAL_MS)

        if self._in_p2():
            self._enter_p2()
            return

        if self.action.count_signal_balls() >= _P1_CLEAR_BALL_MIN:
            self._p1_ticks = 0
            self.phase = "p1_clear"
            return

        self._p1_ticks = 0
        self.phase = "p1_farm"

    def _phase_p1_farm(self) -> None:
        if self._in_p2():
            self._enter_p2()
            return
        if self.action.count_signal_balls() >= _P1_CLEAR_BALL_MIN:
            self._p1_ticks = 0
            self.phase = "p1_clear"
            return

        self.action.continuous_attack(_P1_ATTACK_BURST, _P1_ATTACK_INTERVAL_MS)
        self._p1_ticks += 1
        if self._p1_ticks >= _P1_LOOP_MAX:
            self.phase = "idle"

    def _phase_p1_clear(self) -> None:
        if self._in_p2():
            self._enter_p2()
            return
        if self.action.check_Skill_energy_bar():
            self.phase = "p1_ult"
            return

        self.action.ball_elimination_target(2)
        self.action.ball_elimination_target(1)
        self.action.continuous_attack(_P1_ATTACK_BURST, _P1_ATTACK_INTERVAL_MS)
        self._p1_ticks += 1
        if self._p1_ticks >= _P1_LOOP_MAX:
            self.phase = "idle"

    def _phase_p1_ult(self) -> None:
        self.action.logger.info("骇影: 一阶段大招")
        self.action.use_skill()
        self.phase = "idle"

    def _phase_p2_scan(self) -> None:
        if not self._in_p2():
            self.action.logger.info("骇影: 二阶段结束")
            self._finish_p2()
            return

        if self._p2_ball_active(_P2_RED_NODE):
            self.phase = "p2_red"
            return
        if self._p2_ball_active(_P2_YELLOW_NODE):
            self.phase = "p2_yellow"
            return
        if self._p2_ball_active(_P2_BLUE_NODE):
            self._p2_blue_step = 0
            self.phase = "p2_blue"
            return

        self.action.logger.info("骇影: 二阶段 RGB 均未命中，收尾大招")
        self._p2_ult_fired = False
        self._p2_ult_wait_ticks = 0
        self.phase = "p2_ult"

    def _phase_p2_red(self) -> None:
        self.action.logger.info("骇影: 二阶段红球")
        for _ in range(4):
            self.action.ball_elimination_target(2)
        self.phase = "p2_scan"

    def _phase_p2_yellow(self) -> None:
        self.action.logger.info("骇影: 二阶段黄球")
        for _ in range(_P2_YELLOW_LOOPS):
            self.action.continuous_attack(
                _P2_YELLOW_ATTACK_COUNT, _P2_YELLOW_ATTACK_INTERVAL_MS
            )
            self.action.ball_elimination_target(1)
        self.phase = "p2_scan"

    def _phase_p2_blue(self) -> None:
        if self._p2_blue_step == 0:
            self.action.logger.info("骇影: 二阶段蓝球")
            self.action.long_press_attack(_P2_BLUE_LONG_PRESS_MS)
            self._p2_blue_step = 1
            return

        self.action.ball_elimination_target(1)
        self._p2_blue_step = 0
        self.phase = "p2_scan"

    def _phase_p2_ult(self) -> None:
        if not self._p2_ult_fired:
            self.action.logger.info("骇影: 二阶段收尾大招")
            self.action.use_skill_until_empty(timeout=5)
            self.action.auxiliary_machine()
            self._p2_ult_fired = True
            self._p2_ult_wait_ticks = 0
            return

        if self.action.check_status(_P2_NORMAL_NODE):
            self._p2_ult_wait_ticks += 1
            if self._p2_ult_wait_ticks >= _P2_ULT_WAIT_MAX:
                self.action.logger.info("骇影: 等待普通图标超时，QTE 切人")
                self.action.auxiliary_machine()
                self.action.use_qte()
                self._finish_p2()
            return

        self.action.logger.info("骇影: 普通图标消失，QTE 切人")
        self.action.auxiliary_machine()
        self.action.use_qte()
        self._finish_p2()
