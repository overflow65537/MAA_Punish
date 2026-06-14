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
from typing import Any

from MPAcustom.action.tool.LoadSetting import ROLE_ACTIONS

logger = logging.getLogger(__name__)

TEAM_COLORS = ("R", "B", "Y")

_KNOWN_CLS_NAMES = {
    role_info.get("cls_name")
    for role_info in ROLE_ACTIONS.values()
    if role_info.get("cls_name")
}


@dataclass
class TeamSnapshot:
    """进战识别结果：R/B/Y 色位对应 cls_name，current 为当前上场色位。"""

    R: str
    B: str
    Y: str
    current: str

    def cls_at(self, color: str) -> str:
        key = color.upper()
        if key not in TEAM_COLORS:
            raise KeyError(f"无效色位: {color}")
        return getattr(self, key)

    def current_cls(self) -> str:
        return self.cls_at(self.current)

    def other_colors(self) -> tuple[str, str]:
        cur = self.current.upper()
        return tuple(c for c in TEAM_COLORS if c != cur)  # type: ignore[return-value]

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
        if not r or not b or not y:
            logger.warning("TeamSnapshot cls_name 不能为空")
            return None

        for label, cls_name in (("R", r), ("B", b), ("Y", y)):
            if cls_name not in _KNOWN_CLS_NAMES:
                logger.warning(
                    "TeamSnapshot %s=%s 未在 ROLE_ACTIONS.cls_name 中找到",
                    label,
                    cls_name,
                )

        return cls(R=r, B=b, Y=y, current=current)
