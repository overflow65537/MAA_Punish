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

"""逆冕战斗程序"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_ENERGY_FULL_NODE = "检查逆冕能量即将满"
_ENERGY_EMPTY_NODE = "检查逆冕能量空"
_SPECIAL_BALL_NODE = "检查逆冕特殊球"
_SPECIAL_ATK_TIMEOUT = 5.0
_SKILL_CHARGE_TIMEOUT = 10.0
_SKILL_CAST_MAX = 20
_FARM_MAX_TICKS = 20
_FULL_BALL_THRESHOLD = 16
_SPECIAL_BALL_MIN = 7


class InverseCrown(BaseRole):
    """逆冕：特殊球 → 大招 → 切人。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._special_atk_deadline = 0.0
        self._skill_charge_deadline = 0.0
        self._skill_cast_ticks = 0
        self._skill_sub = ""
        self._skill_switch_after = False
        self._farm_ticks = 0
        self._post_ult_qte_used = False

    def reset_state(self) -> None:
        super().reset_state()
        self._special_atk_deadline = 0.0
        self._skill_charge_deadline = 0.0
        self._skill_cast_ticks = 0
        self._skill_sub = ""
        self._skill_switch_after = False
        self._farm_ticks = 0
        self._post_ult_qte_used = False

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "ball_dump":
            self._phase_ball_dump()
        elif self.phase == "special_press":
            self._phase_special_press()
        elif self.phase == "special_attack":
            self._phase_special_attack()
        elif self.phase == "skill":
            self._phase_skill()
        elif self.phase == "farm":
            self._phase_farm()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _energy_almost_full(self) -> bool:
        return bool(self.action.check_status(_ENERGY_FULL_NODE))

    def _special_ball_ready(self) -> bool:
        return bool(self.action.check_status(_SPECIAL_BALL_NODE))

    def _is_cage_mode(self) -> bool:
        node = self.combat.context.get_node_data("选择角色程序")
        if node is None:
            return False
        return bool(node.get("attach", {}).get("cage", False))

    def _enter_skill(self, *, switch_after: bool) -> None:
        self._skill_switch_after = switch_after
        if self._is_cage_mode():
            self.action.logger.info("cage: True")
            self._skill_sub = "cage"
        else:
            self.action.logger.info("cage: False")
            self._skill_sub = "charge"
            self._skill_charge_deadline = time.monotonic() + _SKILL_CHARGE_TIMEOUT
            self._skill_cast_ticks = 0
        self.phase = "skill"

    def _finish_skill(self) -> None:
        if not self._post_ult_qte_used:
            self.action.auxiliary_machine()
            self.action.use_qte()
            self._post_ult_qte_used = True
        self._skill_sub = ""
        self.phase = "switch" if self._skill_switch_after else "idle"

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        if self._energy_almost_full():
            self.action.logger.info("大招")
            self._enter_skill(switch_after=True)
            return

        ball_count = self.action.count_signal_balls()
        if ball_count >= _FULL_BALL_THRESHOLD:
            self.action.logger.info("球数满足条件，进行球消")
            self.phase = "ball_dump"
            return

        if ball_count > _SPECIAL_BALL_MIN and self._special_ball_ready():
            self.action.logger.info("特殊球就绪")
            self.phase = "special_press"
            return

        self.action.logger.info("特殊球未就绪")
        self._farm_ticks = 0
        self.phase = "farm"

    def _phase_ball_dump(self) -> None:
        self.action.ball_elimination_target()
        self.phase = "idle"

    def _phase_special_press(self) -> None:
        self.combat.context.run_action(
            "长按1号球",
            pipeline_override={"长按1号球": {"duration": 5500}},
        )
        self.action.logger.info("特殊球按下完成")
        self._special_atk_deadline = time.monotonic() + _SPECIAL_ATK_TIMEOUT
        self.phase = "special_attack"

    def _phase_special_attack(self) -> None:
        if self._energy_almost_full() or time.monotonic() >= self._special_atk_deadline:
            self._enter_skill(switch_after=True)
            return
        self.action.attack()

    def _phase_skill(self) -> None:
        if self._skill_sub == "cage":
            self.action.long_press_skill(2000)
            self._finish_skill()
        elif self._skill_sub == "charge":
            if (
                self._energy_almost_full()
                or time.monotonic() >= self._skill_charge_deadline
            ):
                self._skill_sub = "cast"
                self._skill_cast_ticks = 0
            else:
                self.action.attack()
        elif self._skill_sub == "cast":
            self.action.use_skill()
            self._skill_cast_ticks += 1
            if (
                self.action.check_status(_ENERGY_EMPTY_NODE)
                or self._skill_cast_ticks >= _SKILL_CAST_MAX
            ):
                self._skill_sub = "finish"
        elif self._skill_sub == "finish":
            #self.action.long_press_attack(4000)
            self._finish_skill()
        else:
            self.phase = "idle"

    def _phase_farm(self) -> None:
        self.action.attack()
        if self._special_ball_ready():
            self.action.logger.info("特殊球就绪")
            self.phase = "idle"
            return
        self._farm_ticks += 1
        if self._farm_ticks >= _FARM_MAX_TICKS:
            self.phase = "idle"
