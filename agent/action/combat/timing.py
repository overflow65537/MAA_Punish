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
战斗等待：delay 期间不空转，周期性执行 tick（如盲发普攻）。
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

DEFAULT_ACTIVE_TICK = 0.05


def active_delay(
    seconds: float,
    *,
    on_tick: Callable[[], Any] | None = None,
    should_stop: Callable[[], bool] | None = None,
    tick_interval: float = DEFAULT_ACTIVE_TICK,
) -> bool:
    """
    带 tick 的等待。

    每个时间片开始时调用 on_tick（如 attack），避免 sleep 空转。
    返回 False 表示被 should_stop 中断。
    """
    if seconds <= 0:
        if on_tick is not None:
            on_tick()
        return True

    deadline = time.monotonic() + seconds
    while True:
        if should_stop is not None and should_stop():
            return False
        if on_tick is not None:
            on_tick()
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(tick_interval, remaining))
    return True
