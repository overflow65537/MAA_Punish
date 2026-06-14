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
战斗角色 CustomAction（Pipeline JumpBack 入口，委托 BaseRole）
"""

from __future__ import annotations

from maa.context import Context
from maa.custom_action import CustomAction

from MPAcustom.action.combat.core.role_factory import create_role
from MPAcustom.action.combat.core.standalone import StandaloneCombat


class RoleCustomAction(CustomAction):
    """按 cls_name 创建 Role 并跑一轮，供 Pipeline 识别人物后调用。"""

    cls_name: str = ""

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        combat = StandaloneCombat(context)
        role = create_role(combat, "R", self.cls_name)
        role.run_rotation()
        return CustomAction.RunResult(success=True)


class GeneralFight(RoleCustomAction):
    cls_name = "GeneralFight"


class Shukra(RoleCustomAction):
    cls_name = "Shukra"


class CrimsonWeave(RoleCustomAction):
    cls_name = "CrimsonWeave"


class Hyperreal(RoleCustomAction):
    cls_name = "Hyperreal"


class Oblivion(RoleCustomAction):
    cls_name = "Oblivion"


class Stigmata(RoleCustomAction):
    cls_name = "Stigmata"


class LostLullaby(RoleCustomAction):
    cls_name = "LostLullaby"


class Pyroath(RoleCustomAction):
    cls_name = "Pyroath"


class Crepuscule(RoleCustomAction):
    cls_name = "Crepuscule"


class Pianissimo(RoleCustomAction):
    cls_name = "Pianissimo"


class InverseCrown(RoleCustomAction):
    cls_name = "InverseCrown"


class Spectre(RoleCustomAction):
    cls_name = "Spectre"


class Limpidity(RoleCustomAction):
    cls_name = "Limpidity"


class Aegis(RoleCustomAction):
    cls_name = "Aegis"
