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

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from maa.context import Context

COLOR_TO_QTE_NODE: dict[str, str] = {
    "R": "切换红色QTE",
    "B": "切换蓝色QTE",
    "Y": "切换黄色QTE",
}


def click_qte_by_color(
    context: Context, color: str, image: Any | None = None
) -> bool:
    """
    按色位点击 QTE 换人区。不重新识别队伍，只执行点击。

    :param color: R / B / Y
    :param image: 可选，复用 combat.frame
    """
    node = COLOR_TO_QTE_NODE.get(color.upper())
    if not node:
        return False

    if image is None:
        image = context.tasker.controller.post_screencap().wait().get()

    result = context.run_recognition(node, image)
    if not result or not result.hit or not result.best_result:
        return False

    box = result.best_result.box  # type: ignore[attr-defined]
    context.tasker.controller.post_click(box[0], box[1]).wait()
    return True
