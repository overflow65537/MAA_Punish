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

"""ROLE_ACTIONS 启动校验：cls_name、attack_template、模板资源路径。"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from logger_component import LoggerComponent

from action.combat.config.LoadSetting import ROLE_ACTIONS
from action.combat.core.role_factory import ROLE_CLASS_MAP

logger = LoggerComponent(__name__).logger

_IMAGE_ROOTS = (
    Path(__file__).resolve().parents[4] / "resource" / "base" / "image",
    Path(__file__).resolve().parents[4] / "resource" / "pgr_win32" / "image",
)


def _normalize_paths(raw: Any) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [p for p in raw if isinstance(p, str)]
    return []


def _iter_skill_template_paths(skill_template: Any) -> list[str]:
    if not isinstance(skill_template, dict):
        return []
    paths: list[str] = []
    for entry in skill_template.values():
        if not isinstance(entry, dict):
            continue
        for rec_cfg in entry.values():
            if isinstance(rec_cfg, dict):
                paths.extend(_normalize_paths(rec_cfg.get("template")))
    return paths


def _image_exists(relative_path: str) -> bool:
    return any((root / relative_path).is_file() for root in _IMAGE_ROOTS)


def validate_role_actions() -> bool:
    """校验 ROLE_ACTIONS，返回是否全部通过。"""
    ok = True

    seen_cls: set[str] = set()
    for role_key, role_info in ROLE_ACTIONS.items():
        cls_name = role_info.get("cls_name", "")
        if not cls_name:
            logger.error("ROLE_ACTIONS[%s] 缺少 cls_name", role_key)
            ok = False
            continue

        if cls_name not in seen_cls:
            seen_cls.add(cls_name)
            if cls_name not in ROLE_CLASS_MAP:
                logger.error(
                    "ROLE_ACTIONS cls_name=%s 未在 roles 包中找到对应战斗类",
                    cls_name,
                )
                ok = False

        attack_templates = _normalize_paths(role_info.get("attack_template"))
        if not attack_templates:
            logger.error("ROLE_ACTIONS[%s] attack_template 为空", role_key)
            ok = False

        for field in ("template", "attack_template"):
            for rel_path in _normalize_paths(role_info.get(field)):
                if not _image_exists(rel_path):
                    logger.error(
                        "ROLE_ACTIONS[%s].%s 模板不存在: %s",
                        role_key,
                        field,
                        rel_path,
                    )
                    ok = False

        for rel_path in _iter_skill_template_paths(role_info.get("skill_template")):
            if not _image_exists(rel_path):
                logger.error(
                    "ROLE_ACTIONS[%s].skill_template 模板不存在: %s",
                    role_key,
                    rel_path,
                )
                ok = False

    if ok:
        logger.info("ROLE_ACTIONS 配置校验通过（%d 个角色）", len(ROLE_ACTIONS))
    else:
        logger.error("ROLE_ACTIONS 配置校验未通过，请检查上述错误")
    return ok
