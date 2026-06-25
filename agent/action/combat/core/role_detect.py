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

from action.combat.config.LoadSetting import ROLE_ACTIONS


def _normalize_attack_templates(raw: Any) -> list[Any]:
    if not raw:
        return []
    if isinstance(raw, str):
        return [raw]
    return list(raw)


def attack_templates_for_cls(cls_name: str) -> list[Any]:
    """按 cls_name 取 attack_template；未找到返回空列表。"""
    for role_info in ROLE_ACTIONS.values():
        if role_info.get("cls_name") == cls_name:
            return _normalize_attack_templates(role_info.get("attack_template"))
    return []


def match_attack_template(
    context: Context, image: Any, templates: list[Any]
) -> bool:
    """用给定 attack_template 列表匹配当前画面。"""
    if not templates:
        return False
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
    return bool(result and result.hit)


def is_cls_on_field(context: Context, image: Any, cls_name: str) -> bool:
    """仅匹配指定 cls 的 attack_template，判断该角色是否在场。"""
    return match_attack_template(context, image, attack_templates_for_cls(cls_name))


_GENERIC_CLS = "GeneralFight"


def detect_current_role(context: Context, image: Any) -> tuple[str, str]:
    """
    按 attack_template 模板匹配当前上场角色。

    专属 cls 优先于 GeneralFight，避免通用占位误匹配谬影。

    :return: (展示名, cls_name)
    """
    dedicated: list[tuple[str, dict]] = []
    generic: list[tuple[str, dict]] = []
    for role_name, role_info in ROLE_ACTIONS.items():
        templates = _normalize_attack_templates(role_info.get("attack_template"))
        if not templates:
            continue
        cls_name = str(role_info.get("cls_name", "GeneralFight"))
        bucket = generic if cls_name == _GENERIC_CLS else dedicated
        bucket.append((role_name, role_info))

    for role_name, role_info in dedicated + generic:
        templates = _normalize_attack_templates(role_info.get("attack_template"))
        if match_attack_template(context, image, templates):
            display = str(role_info.get("name") or role_name)
            return display, str(role_info.get("cls_name", "GeneralFight"))
    return "未知", "GeneralFight"


def is_switch_arrived(context: Context, image: Any, roster_cls: str) -> bool:
    """
    切人到位判定。

    专属 cls：仅匹配目标 attack_template，未命中视为未到位（不切全 roster）。
    roster 为 GeneralFight：全量 detect_current_role，场上为任意专属角色即视为到位。
    """
    if roster_cls and roster_cls != _GENERIC_CLS:
        return is_cls_on_field(context, image, roster_cls)

    if roster_cls and is_cls_on_field(context, image, roster_cls):
        return True

    display_name, detected_cls = detect_current_role(context, image)
    if display_name == "未知":
        return False

    if roster_cls == _GENERIC_CLS and detected_cls != _GENERIC_CLS:
        return True

    return detected_cls == roster_cls
