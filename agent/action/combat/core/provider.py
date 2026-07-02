# Copyright (c) 2024-2025 MAA_Punish
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, distribute, sublicense, and/or sell
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

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from action.combat.core.role_detect import detect_current_role
from action.combat.core.switch import blind_attack_click
from action.combat.core.switch import detect_visible_team_colors
from action.combat.core.team import (
    TEAM_COLORS,
    TeamSnapshot,
    format_team_snapshot_line,
    load_team_roster_from_context,
)

if TYPE_CHECKING:
    from maa.context import Context

    from action.combat.core.session import CombatTask

logger = logging.getLogger(__name__)

# 退战时优先于「战斗中」检测的固定 overlay 节点（全模式启用）
COMBAT_EXIT_OVERLAY_NODES = ("重启_寒境曙光",)


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

    def match_exit_overlay(self, context: Context, combat: CombatTask) -> str | None:
        """命中固定退战 overlay（如肉鸽重启界面）时返回节点名。"""
        image = self._get_frame(context, combat)
        for name in COMBAT_EXIT_OVERLAY_NODES:
            result = context.run_recognition(name, image)
            if result and result.hit:
                logger.info("识别到战斗退出界面: %s", name)
                return name
        return None

    def in_outer_interface(self, context: Context, combat: CombatTask) -> bool:
        """是否处于战斗外界面（结算、菜单、大地图等）。仅在 in_combat 未命中时调用。"""
        return False

    def detect_team(self, context: Context, combat: CombatTask) -> TeamSnapshot | None:
        """进战后第一次识别队伍。返回 R/B/Y cls_name 及 current 色位。"""
        return None

    def detect_qte_colors(self, context: Context, combat: CombatTask) -> list[str]:
        """当前 QTE 换人区可见且有色位配置的色位（不含 current）。"""
        if combat.team is None or combat.team.is_solo():
            return []
        image = self._get_frame(context, combat)
        visible = set(detect_visible_team_colors(context, image))
        filled = set(combat.team.filled_colors())
        cur = combat.team.current.upper()
        return [
            c
            for c in TEAM_COLORS
            if c != cur and c in filled and c in visible
        ]

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
        部分角色攻击动画会短暂遮挡该 UI，框架侧会容忍连续未命中 8 秒。
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
        进战识别：初次进入默认红色色位（R）为主站。

        色位 roster 从「战斗队伍色位」节点读取；
        节点 attach 为空 → 单人队（仅当前识别到的角色）。
        """
        roster = load_team_roster_from_context(context)
        if roster is None:
            image = self._get_frame(context, combat)
            display_name, cls_name = detect_current_role(
                context,
                image,
                on_tick=lambda: blind_attack_click(context),
            )
            combat.current_role_name = display_name
            logger.info("战斗队伍色位为空，按单人队处理: %s", cls_name)
            return TeamSnapshot.solo(cls_name)

        r_cls = roster.get("R", "")
        if not r_cls:
            logger.warning("战前 roster R 色位为空，按 solo 处理: %s", roster)
            return TeamSnapshot.solo(roster.get("B") or roster.get("Y") or "GeneralFight")

        snapshot = TeamSnapshot.from_dict(
            {
                "R": roster["R"],
                "B": roster["B"],
                "Y": roster["Y"],
                "current": "R",
            }
        )
        if snapshot is None:
            return TeamSnapshot.solo(r_cls)

        logger.info(format_team_snapshot_line(snapshot))
        return snapshot
