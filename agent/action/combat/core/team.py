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
MAA_Punish 战斗队伍色位快照
作者:overflow65537
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from action.combat.config.LoadSetting import ROLE_ACTIONS

if TYPE_CHECKING:
    from maa.context import Context

logger = logging.getLogger(__name__)

TEAM_COLORS = ("R", "B", "Y")
TEAM_ROSTER_NODE = "战斗队伍色位"

_KNOWN_CLS_NAMES = {
    role_info.get("cls_name")
    for role_info in ROLE_ACTIONS.values()
    if role_info.get("cls_name")
}


def role_display_name_to_cls(role_name: str | None) -> str:
    """RoleSelection 角色名 → cls_name；空位返回空字符串。"""
    if not role_name:
        return ""
    base_name = role_name.replace("[试用]", "").strip()
    if not base_name:
        return ""
    role_info = ROLE_ACTIONS.get(base_name, {})
    return str(role_info.get("cls_name", "")).strip()


def roster_from_role_selection(
    attacker: str | None,
    tank: str | None,
    support: str | None,
) -> dict[str, str]:
    """战前配队：进攻→R，装甲→Y，支援→B。"""
    return {
        "R": role_display_name_to_cls(attacker),
        "Y": role_display_name_to_cls(tank),
        "B": role_display_name_to_cls(support),
    }


def publish_team_roster(context: Context, roster: dict[str, str]) -> None:
    """RoleSelection 完成后写入 Pipeline attach，供战斗内读取。"""
    attach = {color: str(roster.get(color, "")).strip() for color in TEAM_COLORS}
    context.override_pipeline({TEAM_ROSTER_NODE: {"attach": attach}})
    logger.info("写入 %s: %s", TEAM_ROSTER_NODE, attach)


def load_team_roster_from_context(context: Context) -> dict[str, str] | None:
    """
    从 Pipeline 节点读取战前色位。

    attach 缺失或 R/B/Y 全空 → None（视为单人队、无轮切）。
    """
    node = context.get_node_data(TEAM_ROSTER_NODE) or {}
    attach = node.get("attach")
    if not isinstance(attach, dict):
        return None

    roster = {
        color: str(attach.get(color, "")).strip() for color in TEAM_COLORS
    }
    if not any(roster.values()):
        return None
    return roster


@dataclass
class TeamSnapshot:
    """进战结果：R/B/Y 色位 cls_name（空字符串表示该位无人），current 为当前主站色位。"""

    R: str
    B: str
    Y: str
    current: str

    def cls_at(self, color: str) -> str:
        key = color.upper()
        if key not in TEAM_COLORS:
            raise KeyError(f"无效色位: {color}")
        return getattr(self, key).strip()

    def current_cls(self) -> str:
        return self.cls_at(self.current)

    def filled_colors(self) -> tuple[str, ...]:
        return tuple(c for c in TEAM_COLORS if self.cls_at(c))

    def other_colors(self) -> tuple[str, ...]:
        cur = self.current.upper()
        return tuple(c for c in TEAM_COLORS if c != cur)

    def other_filled_colors(self) -> tuple[str, ...]:
        cur = self.current.upper()
        return tuple(c for c in TEAM_COLORS if c != cur and self.cls_at(c))

    def is_solo(self) -> bool:
        """仅一个有效色位 → 单人队，不轮切。"""
        return len(self.filled_colors()) <= 1

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TeamSnapshot | None:
        if not isinstance(data, dict):
            return None

        missing = [k for k in (*TEAM_COLORS, "current") if k not in data]
        if missing:
            logger.warning("TeamSnapshot 缺少字段: %s", missing)
            return None

        current = str(data["current"]).upper()
        if current not in TEAM_COLORS:
            logger.warning("TeamSnapshot current 无效: %s", data["current"])
            return None

        r = str(data["R"]).strip()
        b = str(data["B"]).strip()
        y = str(data["Y"]).strip()

        for label, cls_name in (("R", r), ("B", b), ("Y", y)):
            if cls_name and cls_name not in _KNOWN_CLS_NAMES:
                logger.warning(
                    "TeamSnapshot %s=%s 未在 ROLE_ACTIONS.cls_name 中找到",
                    label,
                    cls_name,
                )

        current_cls = (r, b, y)[TEAM_COLORS.index(current)]
        if not current_cls:
            logger.warning(
                "TeamSnapshot current=%s 对应色位 cls 为空", current
            )
            return None

        return cls(R=r, B=b, Y=y, current=current)

    @classmethod
    def solo(cls, cls_name: str, *, current: str = "R") -> TeamSnapshot:
        """无战前 roster 或仅主站识别时使用。"""
        current = current.upper()
        roster = {c: "" for c in TEAM_COLORS}
        roster[current] = cls_name
        return cls(R=roster["R"], B=roster["B"], Y=roster["Y"], current=current)
