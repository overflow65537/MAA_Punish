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
MAA_Punish 战斗角色工厂
作者:overflow65537
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from MPAcustom.action.combat.role import BaseRole
from MPAcustom.action.combat.roles.general import GeneralRole

if TYPE_CHECKING:
    from MPAcustom.action.combat.session import CombatTask

ROLE_CLASS_MAP: dict[str, type[BaseRole]] = {
    "GeneralFight": GeneralRole,
}


def create_role(combat: CombatTask, color: str, cls_name: str) -> BaseRole:
    role_cls = ROLE_CLASS_MAP.get(cls_name, GeneralRole)
    return role_cls(combat, color, cls_name)
