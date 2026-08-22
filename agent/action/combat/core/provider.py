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

from action.combat.core.role import resolve_cls_label
from action.combat.core.role_detect import detect_current_role
from action.combat.core.switch import (
    CHAR_CHECK_ATTACK_COUNT,
    blind_attack_click,
    detect_visible_team_colors,
)
from action.combat.core.team import (
    GENERIC_CLS_NAME,
    TEAM_COLORS,
    TeamSnapshot,
    entry_qte_bench_colors,
    format_team_snapshot_line,
    load_team_roster_from_context,
    roster_from_entry_qte,
    should_infer_team_size_from_qte,
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
        """
        进战识别：场上第一人固定为红位。

        先看选人名单：但凡有一个专属战斗逻辑，直接采用该名单。
        名单全是通用作战（或没有名单）时，先识别场上角色，再按黄/蓝 QTE 判断人数。
        """
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
        进战识别：场上第一人固定为红位。

        先看选人名单：但凡有一个专属战斗逻辑，直接采用该名单。
        名单全是通用作战（或没有名单）时，先识别场上角色，再截一帧看黄/蓝 QTE 定人数。
        """
        published = load_team_roster_from_context(context)
        if not should_infer_team_size_from_qte(published):
            snapshot = TeamSnapshot.from_dict({**(published or {}), "current": "R"})
            if snapshot is None:
                fallback = (published or {}).get("R") or GENERIC_CLS_NAME
                logger.warning("选人名单无法组成队伍，按单人队: %s", published)
                return TeamSnapshot.solo(fallback)
            combat.current_role_name = resolve_cls_label(snapshot.R)
            logger.info("进战采用选人名单，跳过 QTE 人数判断")
            logger.info(format_team_snapshot_line(snapshot))
            return snapshot

        image = self._get_frame(context, combat)
        prefer: list[str] = []
        if published:
            for color in TEAM_COLORS:
                cls_name = str(published.get(color) or "").strip()
                if cls_name and cls_name not in prefer:
                    prefer.append(cls_name)
        display_name, field_cls = detect_current_role(
            context,
            image,
            prefer_cls=prefer,
            on_tick=lambda: blind_attack_click(
                context, attack_count=CHAR_CHECK_ATTACK_COUNT
            ),
        )
        combat.current_role_name = display_name

        combat.frame = None
        image = self._get_frame(context, combat)
        visible_qte = detect_visible_team_colors(context, image)

        roster = roster_from_entry_qte(field_cls, visible_qte, published)
        bench = entry_qte_bench_colors(visible_qte)
        if len(bench) >= 2:
            team_type = "三人队"
        elif len(bench) == 1:
            team_type = "两人队"
        else:
            team_type = "单人队"
        logger.info(
            "进战 QTE 检查: 可见=%s → %s",
            ",".join(bench) or "无",
            team_type,
        )

        snapshot = TeamSnapshot.from_dict({**roster, "current": "R"})
        if snapshot is None:
            return TeamSnapshot.solo(roster.get("R") or field_cls or GENERIC_CLS_NAME)

        logger.info(format_team_snapshot_line(snapshot))
        return snapshot
