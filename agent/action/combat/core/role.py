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

"""
MAA_Punish
MAA_Punish 战斗角色策略基类
作者:overflow65537
"""

from __future__ import annotations

import time
from enum import StrEnum
from typing import TYPE_CHECKING

from action.combat.actions.CombatActions import CombatActions
from action.combat.config.LoadSetting import ROLE_ACTIONS

if TYPE_CHECKING:
    from action.combat.core.session import CombatTask


class SwitchPriority(StrEnum):
    NORMAL = "normal"
    MUST = "must"
    NO = "no"


def resolve_role_name(cls_name: str) -> str:
    """按 cls_name 反查 ROLE_ACTIONS，供 CombatActions 加载 skill_template。"""
    for role_key, role_info in ROLE_ACTIONS.items():
        if role_info.get("cls_name") == cls_name:
            return role_info.get("name") or role_key
    return cls_name


class BaseRole:
    """角色策略基类：组合 CombatActions，通过 CombatTask 切人。"""

    SWITCH_PHASE = "switch"

    # 非 None 时覆盖 CombatTask.SWITCH_VERIFY_TIMEOUT（单次切人 QTE 尝试窗口）
    switch_verify_timeout: float | None = None

    def __init__(self, combat: CombatTask, color: str, cls_name: str):
        self.combat = combat
        self.color = color.upper()
        self.cls_name = cls_name
        self.phase = "idle"
        self.action = CombatActions(
            combat.context,
            role_name=resolve_role_name(cls_name),
            skip_combat_gate=True,
        )
        self.action._role = self

    def perform(self) -> None:
        if self.phase == self.SWITCH_PHASE:
            self.combat.request_role_switch(self)
            return
        if self.phase == "idle" and self.combat.refresh_field_role_on_idle(self):
            return
        self.do_perform()

    def do_perform(self) -> None:
        self.action.attack()

    def on_switch_succeeded(self) -> None:
        """切人成功后的角色侧收尾（默认 reset_state 已回到 idle）。"""

    def on_switch_failed(self) -> None:
        """切人失败后的回落 phase。"""
        self.phase = "idle"

    def get_switch_priority(
        self, requester: BaseRole, has_intro: bool = False
    ) -> SwitchPriority:
        return SwitchPriority.NORMAL

    def switch_red(self) -> bool:
        """切换到红色位（进攻）。"""
        return self._switch_to_color("R")

    def switch_yellow(self) -> bool:
        """切换到黄色位（装甲）。"""
        return self._switch_to_color("Y")

    def switch_blue(self) -> bool:
        """切换到蓝色位（支援）。"""
        return self._switch_to_color("B")

    def _switch_to_color(self, color: str) -> bool:
        if self.combat.is_switch_disabled():
            return False
        return self.combat.switch_to_color(color, attacker=self)

    def switch_next(self) -> bool:
        """请求战斗管理器切到下一合适角色。"""
        return self.combat.request_role_switch(self)

    def reset_state(self) -> None:
        self.phase = "idle"
