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

from MPAcustom.action.combat.actions.CombatActions import CombatActions
from MPAcustom.action.combat.config.LoadSetting import ROLE_ACTIONS

if TYPE_CHECKING:
    from MPAcustom.action.combat.core.session import CombatTask


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

    def perform(self) -> None:
        self.do_perform()

    def do_perform(self) -> None:
        self.action.attack()

    def get_switch_priority(
        self, requester: BaseRole, has_intro: bool = False
    ) -> SwitchPriority:
        return SwitchPriority.NORMAL

    def switch_next(self) -> bool:
        """请求战斗管理器切到下一合适角色（受 Pipeline「自动切换」开关控制）。"""
        if not self.combat.is_switch_enabled():
            self.action.logger.info("未开启切换角色功能")
            return False
        if not self.combat.can_switch():
            return False
        target_color = self.combat.choose_switch_color(self)
        if not target_color:
            return False
        if self.combat.switch_to_color(target_color):
            self.reset_state()
            return True
        self.action.logger.warning("切人失败")
        return False

    def reset_state(self) -> None:
        self.phase = "idle"
