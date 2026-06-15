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
MAA_Punish 战斗角色工厂
作者:overflow65537

约定：roles 包内类名与 LoadSetting.ROLE_ACTIONS.cls_name 一致。
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from typing import TYPE_CHECKING

from MPAcustom.action.combat.core.role import BaseRole

if TYPE_CHECKING:
    from MPAcustom.action.combat.core.session import CombatTask

logger = logging.getLogger(__name__)

_DEFAULT_CLS_NAME = "GeneralFight"


def _discover_role_classes() -> dict[str, type[BaseRole]]:
    import MPAcustom.action.combat.roles as roles_pkg

    mapping: dict[str, type[BaseRole]] = {}
    for modinfo in pkgutil.iter_modules(roles_pkg.__path__):
        if modinfo.name.startswith("_"):
            continue
        module = importlib.import_module(f"{roles_pkg.__name__}.{modinfo.name}")
        for attr_name in dir(module):
            role_cls = getattr(module, attr_name)
            if not isinstance(role_cls, type):
                continue
            if not issubclass(role_cls, BaseRole) or role_cls is BaseRole:
                continue
            cls_name = role_cls.__name__
            if cls_name in mapping:
                logger.warning(
                    "重复注册 cls_name=%s: %s 与 %s",
                    cls_name,
                    mapping[cls_name].__name__,
                    role_cls.__name__,
                )
            mapping[cls_name] = role_cls
    return mapping


ROLE_CLASS_MAP: dict[str, type[BaseRole]] = _discover_role_classes()


def create_role(combat: CombatTask, color: str, cls_name: str) -> BaseRole:
    role_cls = ROLE_CLASS_MAP.get(cls_name)
    if role_cls is None:
        logger.debug("未找到 %s，兜底 %s", cls_name, _DEFAULT_CLS_NAME)
        role_cls = ROLE_CLASS_MAP.get(_DEFAULT_CLS_NAME)
    if role_cls is None:
        raise RuntimeError(f"缺少默认角色策略: {_DEFAULT_CLS_NAME}")
    return role_cls(combat, color, cls_name)
