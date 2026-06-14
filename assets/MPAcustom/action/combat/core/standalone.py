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
Pipeline CustomAction 专用轻量 CombatTask（单角色跑一轮）
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from MPAcustom.action.combat.core.provider import BaseCombatCheck
from MPAcustom.action.combat.core.session import CombatTask

if TYPE_CHECKING:
    from maa.context import Context


class _AlwaysInCombatCheck(BaseCombatCheck):
    def in_combat(self, context: Context, combat: CombatTask) -> bool:
        return True


class StandaloneCombat(CombatTask):
    """Pipeline JumpBack 链路：不跑完整 combat_once，仅承载 Role 策略。"""

    single_shot = True

    def __init__(self, context: Context):
        super().__init__(context, _AlwaysInCombatCheck())
        self.combat_ui_visible = True
        self.frame: Any | None = None
