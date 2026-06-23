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

"""???????????"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from action.combat.core.role import BaseRole


def complete_rotation(role: BaseRole) -> None:
    """Pipeline ???????CombatRunner ?????? main?"""
    if getattr(role.combat, "single_shot", False):
        role.phase = "done"
    else:
        role.phase = "main"


def combat_start(role: BaseRole, *, next_phase: str = "main") -> bool:
    """idle ????? + ??????? phase??? True ??? tick ????"""
    if role.phase != "idle":
        return False
    role.action.lens_lock()
    role.action.attack()
    role.phase = next_phase
    return True


def done_attack(role: BaseRole) -> bool:
    """done ????????? True ??? tick ????"""
    if role.phase != "done":
        return False
    role.action.attack()
    return True


def finish_switch(role: BaseRole, *, attack_first: bool = False) -> None:
    if attack_first:
        role.action.attack()
    role.action.use_qte()
    role.switch_next()
    role.phase = "done"


def timed_out(deadline: float | None) -> bool:
    return deadline is not None and time.monotonic() >= deadline


def set_deadline(seconds: float) -> float:
    return time.monotonic() + seconds
