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
MAA_Punish 战斗中识别当前角色（复用 Pipeline「检查角色」）
作者:overflow65537
"""

from __future__ import annotations

from typing import Any

from maa.context import Context

from MPAcustom.action.combat.config.LoadSetting import ROLE_ACTIONS


def detect_current_role(context: Context, image: Any) -> tuple[str, str]:
    """
    按 attack_template 模板匹配当前上场角色。

    :return: (ROLE_ACTIONS 键名/展示名, cls_name)
    """
    for role_name, role_info in ROLE_ACTIONS.items():
        templates = role_info.get("attack_template") or []
        if not templates:
            continue
        result = context.run_recognition(
            entry="检查角色",
            image=image,
            pipeline_override={
                "检查角色": {
                    "recognition": {
                        "param": {
                            "template": templates,
                            "threshold": [0.8] * len(templates),
                        },
                    }
                },
            },
        )
        if result and result.hit:
            return role_name, str(role_info.get("cls_name", "GeneralFight"))
    return "未知", "GeneralFight"
