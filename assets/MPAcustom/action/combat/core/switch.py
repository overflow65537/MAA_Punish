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
MAA_Punish 战斗换人 QTE 点击
作者:overflow65537
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from maa.context import Context

COLOR_TO_QTE_NODE: dict[str, str] = {
    "R": "切换红色QTE",
    "B": "切换蓝色QTE",
    "Y": "切换黄色QTE",
}

_CLICK_QTE_MAX_LOOPS = 100


def detect_visible_team_colors(
    context: Context, image: Any | None = None
) -> list[str]:
    """
    扫描当前可见的换人 QTE，返回 R/B/Y 列表（按屏幕 y 从上到下）。
    """
    if image is None:
        image = context.tasker.controller.post_screencap().wait().get()

    candidates: list[tuple[float, str]] = []
    for color, node in COLOR_TO_QTE_NODE.items():
        result = context.run_recognition(node, image)
        if result and result.hit and result.best_result:
            box = result.best_result.box  # type: ignore[attr-defined]
            center_y = box[1] + box[3] / 2
            candidates.append((center_y, color))

    candidates.sort(key=lambda item: item[0])
    return [color for _, color in candidates]


def choose_general_rotation_color(
    context: Context, image: Any | None = None
) -> str | None:
    """
    通用轮换：按 QTE目标.post_delay 在上/下可见 QTE 间交替（对齐旧 switch()）。
    """
    visible = detect_visible_team_colors(context, image)
    if not visible:
        return None

    target_node = context.get_node_data("QTE目标")
    if not target_node:
        return None

    target = int(target_node.get("post_delay", 0))
    if target == 0:
        chosen = visible[-1]
        next_target = 1
    elif target == 1:
        chosen = visible[0]
        next_target = 0
    else:
        return None

    context.override_pipeline({"QTE目标": {"post_delay": next_target}})
    return chosen


def _recognize_qte(
    context: Context, color: str, image: Any | None
) -> Any | None:
    node = COLOR_TO_QTE_NODE.get(color.upper())
    if not node:
        return None
    if image is None:
        image = context.tasker.controller.post_screencap().wait().get()
    result = context.run_recognition(node, image)
    if result and result.hit and result.best_result:
        return result
    return None


def click_qte_by_color(
    context: Context, color: str, image: Any | None = None
) -> bool:
    """按色位点击 QTE 换人区一次。"""
    result = _recognize_qte(context, color, image)
    if not result:
        return False

    box = result.best_result.box  # type: ignore[attr-defined]
    context.tasker.controller.post_click(box[0], box[1]).wait()
    return True


def click_qte_until_done(
    context: Context,
    color: str,
    image: Any | None = None,
    *,
    tick_callback: Callable[[], None] | None = None,
    max_loops: int = _CLICK_QTE_MAX_LOOPS,
) -> bool:
    """
    点击 QTE 并在动画期间持续跟进，直到 QTE 区消失（对齐旧 switch _click_qte）。
    """
    if not click_qte_by_color(context, color, image):
        return False

    for _ in range(max_loops):
        if tick_callback is not None:
            tick_callback()
        image = context.tasker.controller.post_screencap().wait().get()
        result = _recognize_qte(context, color, image)
        if result:
            box = result.best_result.box  # type: ignore[attr-defined]
            context.tasker.controller.post_click(box[0], box[1]).wait()
        else:
            return True

    return True
