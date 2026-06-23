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
MAA_Punish 战斗换人 QTE（QTE.onnx 模型）
作者:overflow65537
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from action.combat.core.role_detect import is_cls_on_field
from action.combat.timing import active_delay

if TYPE_CHECKING:
    from maa.context import Context

# QTE.onnx 标签：
#   0 red_qte / 1 red_qte_ready   —— 换人 vs 放 QTE 技能
#   2 yellow_qte / 3 yellow_qte_ready
#   4 blue_qte / 5 blue_qte_ready
# 切人只匹配 *_qte；*_qte_ready 用于释放 QTE 技能。
COLOR_TO_SWITCH_CLASS: dict[str, int] = {
    "R": 0,
    "Y": 2,
    "B": 4,
}

COLOR_TO_SKILL_CLASS: dict[str, int] = {
    "R": 1,
    "Y": 3,
    "B": 5,
}

COLOR_TO_QTE_NODE: dict[str, str] = {
    "R": "切换红色QTE",
    "B": "切换蓝色QTE",
    "Y": "切换黄色QTE",
}

COLOR_TO_LOWCODE_NODE: dict[str, str] = {
    "R": "切换红",
    "Y": "切换黄",
    "B": "切换蓝",
}

_CLICK_QTE_MAX_LOOPS = 100
_DEFAULT_VERIFY_TIMEOUT = 1.0
_DEFAULT_VERIFY_POLL = 0.05
_QTE_CLICK_BURST = 3


def _box_center(box: Any) -> tuple[int, int]:
    return int(box[0] + box[2] / 2), int(box[1] + box[3] / 2)


def _click_box(context: Context, box: Any) -> None:
    x, y = _box_center(box)
    context.tasker.controller.post_click(x, y).wait()


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


def click_qte_by_color(
    context: Context, color: str, image: Any | None = None, *, burst: int = 1
) -> bool:
    """按色位持续点击 QTE 换人区（QTE.onnx），默认可连点 burst 次。"""
    result = _recognize_qte(context, color, image)
    if not result:
        return False

    box = result.best_result.box  # type: ignore[attr-defined]
    for _ in range(max(1, burst)):
        _click_box(context, box)
    return True


def attempt_switch_to_color(
    context: Context,
    color: str,
    target_cls: str,
    *,
    attacker_callback: Callable[[], None] | None = None,
    verify_timeout: float = _DEFAULT_VERIFY_TIMEOUT,
    poll_interval: float = _DEFAULT_VERIFY_POLL,
    should_stop: Callable[[], bool] | None = None,
) -> bool:
    """
    在 verify_timeout 内持续盲发普攻 + 持续点击目标 QTE；
    一旦 attack_template 识别到目标角色即成功，超时仍未切换则失败。
    """
    target = color.upper()
    deadline = time.monotonic() + verify_timeout

    def tick() -> None:
        if attacker_callback is not None:
            attacker_callback()

    while time.monotonic() < deadline:
        if should_stop is not None and should_stop():
            return False

        tick()

        image = context.tasker.controller.post_screencap().wait().get()
        if is_cls_on_field(context, image, target_cls):
            return True

        click_qte_by_color(context, target, image, burst=_QTE_CLICK_BURST)

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        if not active_delay(
            min(poll_interval, remaining),
            on_tick=tick,
            should_stop=should_stop,
        ):
            return False

    return False


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
            for _ in range(_QTE_CLICK_BURST):
                _click_box(context, box)
        else:
            return True
        if not active_delay(
            _DEFAULT_VERIFY_POLL,
            on_tick=tick_callback,
        ):
            return False

    return True
