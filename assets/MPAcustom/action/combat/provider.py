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
MAA_Punish 战斗识别
作者:overflow65537
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from MPAcustom.action.combat.team import TeamSnapshot

if TYPE_CHECKING:
    from maa.context import Context

    from MPAcustom.action.combat.session import CombatTask


class BaseCombatCheck(ABC):
    """战斗识别基类。"""

    def _get_frame(self, context: Context, combat: CombatTask) -> Any:
        """优先复用 combat.frame，避免同轮循环重复截屏。"""
        if combat.frame is not None:
            return combat.frame
        combat.frame = context.tasker.controller.post_screencap().wait().get()
        return combat.frame

    @abstractmethod
    def in_combat(self, context: Context, combat: CombatTask) -> bool:
        """是否识别到战斗 UI（如闪避键）。动画遮挡导致短暂未命中时，框架不会立刻退战。"""

    def in_outer_interface(self, context: Context, combat: CombatTask) -> bool:
        """是否处于战斗外界面（结算、菜单、大地图等）。仅在 in_combat 未命中时调用。"""
        return False

    def detect_team(self, context: Context, combat: CombatTask) -> TeamSnapshot | None:
        """进战后第一次识别队伍。返回 R/B/Y cls_name 及 current 色位。"""
        return None

    def detect_qte_colors(self, context: Context, combat: CombatTask) -> list[str]:
        """当前 QTE 换人区可见色位（最多 2 个）。默认：除 current 外两色。"""
        if combat.team is None:
            return []
        return list(combat.team.other_colors())

    def combat_end_condition(self, context: Context, combat: CombatTask) -> bool:
        """额外结束条件（如 Boss 死亡、任务完成）。默认不主动结束。"""
        return False

    def check_battle_state(self, context: Context, combat: CombatTask) -> str:
        """战斗状态识别（阶段、大招、切人等）。Phase 1 仅写入 combat，不参与分支。"""
        return "unknown"

    def on_combat_check(self, context: Context, combat: CombatTask) -> bool:
        """每轮循环前置校验。返回 False 则强制退战。"""
        return True


class CombatCheck(BaseCombatCheck):
    """战斗识别实现。在此类中编写/调整识别逻辑。"""

    def in_combat(self, context: Context, combat: CombatTask) -> bool:
        """
        是否识别到战斗 UI。

        默认复用 Pipeline 节点「战斗中」（闪避键模板）。
        部分角色攻击动画会短暂遮挡该 UI，框架侧会容忍连续未命中 20 秒。
        """
        image = self._get_frame(context, combat)
        result = context.run_recognition("战斗中", image)
        return bool(result and result.hit)

    def in_outer_interface(self, context: Context, combat: CombatTask) -> bool:
        """
        是否处于战斗外界面。命中后立即退战。

        仅在 in_combat 未命中时由框架调用；可复用 combat.frame。
        """
        image = self._get_frame(context, combat)
        result = context.run_recognition("返回主菜单", image)
        return bool(result and result.hit)

    def detect_team(self, context: Context, combat: CombatTask) -> TeamSnapshot | None:
        """
        进战后识别 R/B/Y 色位与 cls_name。

        在此实现并返回 TeamSnapshot.from_dict({...})，例如：
        {"R": "CrimsonWeave", "B": "Shukra", "Y": "Hyperreal", "current": "R"}
        """
        return None
