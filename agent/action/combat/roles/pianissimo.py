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

"""希声战斗程序

状态机概览::

    idle ──球>5──► p1_clear ──► p1_core(长按) ──► p1_burst(消球1优先) ──► idle
      │                              长按攻击触发核心被动
      ├──球不足──► p1_farm
      └──2阶段──► p2_farm(盲打1s) ──► p2_core ──► p2_burst ──► p2_farm ──► switch
                    │特球(红/黄)──► p2_ult ──► switch   （farm/burst 中亦可打断）
                    │长闪色块──► 长按闪避 700ms
"""

from __future__ import annotations

import time
from collections.abc import Callable

from action.combat.core.role import BaseRole

_PHASE2_NODE = "检查希声2阶段"
_RED_BALL_NODE = "检查希声红球"
_LONG_DODGE_NODE = "检查希声长闪"
_CLEAR_TIMEOUT = 10.0  # 消球阶段最长等待（秒）
_P1_BALL_MIN = 5  # 1 阶段开始消球所需最少信号球
_P1_CORE_BURST = 15  # 1 阶段核心后 burst 轮数（每轮 combat 循环 1 tick）
_P2_CORE_BURST = 20  # 2 阶段核心后 burst 轮数
_P2_LONG_DODGE_MS = 700
_P1_FARM_MAX = 30  # 1 阶段攒球最多 tick，防止无限 farm
_FARM_TICK_MS = 25.0  # 持续普攻间隔（毫秒）
_ATTACK_BURST_S = 0.5  # p1 兜底持续普攻窗口（秒）
_P2_FARM_S = 1.0  # p2 farm：盲打 + 消球2 窗口（秒）
_SWITCH_VERIFY_TIMEOUT = 15.0  # 希声切人动画较长，QTE 尝试窗口


class Pianissimo(BaseRole):
    """希声：1 阶段攒球消球开核心 → 2 阶段 farm 盲打消球2 → 核心 burst → 收尾切人。"""

    switch_verify_timeout = _SWITCH_VERIFY_TIMEOUT

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._clear_deadline = 0.0
        self._burst_ticks = 0
        self._burst_total = 0
        self._farm_ticks = 0
        self._core_started_at = 0.0
        self._p2_farm_next = "p2_core"

    def reset_state(self) -> None:
        super().reset_state()
        self._clear_deadline = 0.0
        self._burst_ticks = 0
        self._burst_total = 0
        self._farm_ticks = 0
        self._core_started_at = 0.0
        self._p2_farm_next = "p2_core"

    def _log_step(self, step: str, **extra: object) -> None:
        """核心/burst 分步计时日志，便于定位长按后消球1延迟。"""
        now = time.monotonic()
        parts = [
            f"希声[{self.phase}] loop={self.combat.loop_count} step={step}",
        ]
        if self._core_started_at:
            parts.append(f"since_core={int((now - self._core_started_at) * 1000)}ms")
        for key, value in extra.items():
            parts.append(f"{key}={value}")
        self.action.logger.info(" ".join(parts))

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "p1_farm":
            self._phase_p1_farm()
        elif self.phase == "p1_clear":
            self._phase_p1_clear()
        elif self.phase == "p1_core":
            self._phase_p1_core()
        elif self.phase == "p1_burst":
            self._phase_p1_burst()
        elif self.phase == "p2_farm":
            self._phase_p2_farm()
        elif self.phase == "p2_core":
            self._phase_p2_core()
        elif self.phase == "p2_burst":
            self._phase_p2_burst()
        elif self.phase == "p2_ult":
            self._phase_p2_ult()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _in_phase2(self) -> bool:
        return bool(self.action.check_status(_PHASE2_NODE))

    def _red_ball_ready(self) -> bool:
        return bool(self.action.check_status(_RED_BALL_NODE))

    def _try_p2_long_dodge(self) -> bool:
        """大招未就绪时：p2 长闪色块命中则长按闪避。"""
        if not self.action.check_status(_LONG_DODGE_NODE):
            return False
        self.action.logger.info("希声2阶段长闪")
        self.action.long_press_dodge(_P2_LONG_DODGE_MS)
        return True

    def _tap_attack(self) -> None:
        """普通攻击：只点攻击键，去掉识别和节点额外等待。"""
        self.action.context.override_pipeline(
            {"攻击": {"pre_delay": 0, "post_delay": 0, "rate_limit": 0}}
        )
        self.action.context.run_action("攻击")

    def _tap_ball(self, slot: int) -> None:
        """盲按消球位，不走排球识别。"""
        node = f"消球{slot}"
        self.action.context.override_pipeline(
            {node: {"pre_delay": 0, "post_delay": 0, "rate_limit": 0}}
        )
        self.action.context.run_action(node)

    def _continuous_tap_attack(
        self,
        *,
        duration_s: float = _ATTACK_BURST_S,
        should_stop: Callable[[], bool] | None = None,
    ) -> None:
        """兜底持续普攻：窗口内按间隔连点，避免每 tick 只打一刀。"""
        deadline = time.monotonic() + duration_s
        interval_s = _FARM_TICK_MS / 1000
        while time.monotonic() < deadline:
            if self.combat.context.tasker.stopping:
                return
            if should_stop is not None and should_stop():
                return
            self._tap_attack()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(interval_s, remaining))

    def _p2_farm_burst(self) -> None:
        """p2 farm：1 秒内持续普攻 + 盲按消球2，不做任何识别。"""
        deadline = time.monotonic() + _P2_FARM_S
        interval_s = _FARM_TICK_MS / 1000
        while time.monotonic() < deadline:
            if self.combat.context.tasker.stopping:
                return
            self._tap_attack()
            self._tap_ball(2)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(interval_s, remaining))

    def _enter_p2_ult(self, *, reason: str) -> None:
        """2 阶段检测到红/黄特球，进入开大 → 切人。"""
        self.action.logger.info("希声2阶段开大 (%s)", reason)
        self.phase = "p2_ult"

    def _begin_clear(self, *, next_phase: str) -> None:
        """进入消球阶段并启动超时计时。"""
        self._clear_deadline = time.monotonic() + _CLEAR_TIMEOUT
        self.phase = next_phase

    def _begin_p2_farm(self, *, next_after: str) -> None:
        """进入 p2 farm；盲打结束后按球数分流到 next_after。"""
        self._clear_deadline = time.monotonic() + _CLEAR_TIMEOUT
        self._p2_farm_next = next_after
        self.phase = "p2_farm"

    def _clear_expired(self) -> bool:
        return time.monotonic() >= self._clear_deadline

    def _begin_burst(self, total: int, next_after: str) -> None:
        """初始化 burst 计数并切换到 burst 阶段。"""
        self._burst_total = total
        self._burst_ticks = 0
        self.phase = next_after

    def _phase_idle(self) -> None:
        # 日常：锁视角后持续普攻，再按球数/阶段分流
        self.action.lens_lock()
        self._continuous_tap_attack()

        if self._in_phase2():
            self.action.logger.info("希声2阶段")
            if self._red_ball_ready():
                self._enter_p2_ult(reason="idle")
                return
            if self._try_p2_long_dodge():
                return
            self._begin_p2_farm(next_after="p2_core")
            return

        if self.action.count_signal_balls() > _P1_BALL_MIN:
            self.action.logger.info("希声1阶段")
            self._begin_clear(next_phase="p1_clear")
            return

        self.action.logger.info("希声1阶段信号球不足")
        self._farm_ticks = 0
        self.phase = "p1_farm"

    def _phase_p1_farm(self) -> None:
        if self._in_phase2() or self.action.count_signal_balls() > _P1_BALL_MIN:
            self.phase = "idle"
            return

        self._continuous_tap_attack()
        self._farm_ticks += 1
        if self._farm_ticks >= _P1_FARM_MAX:
            self.phase = "idle"

    def _phase_p1_clear(self) -> None:
        # 1 阶段消球；中途进 2 阶段则交 idle 重新分流
        if self._in_phase2():
            self.phase = "idle"
            return
        if not self.action.count_signal_balls() or self._clear_expired():
            self.action.logger.info("希声1阶段消球结束")
            self.phase = "p1_core"
            return

        self._continuous_tap_attack()
        target = self.action.Arrange_Signal_Balls()
        if target == -1:
            target = -2
        self.action.ball_elimination_target(target)
        self.action.logger.debug("希声1阶段消球 target=%s", target)

    def _phase_p1_core(self) -> None:
        # 核心被动：长按后立即进 burst（QTE/辅助机挪到 burst 结束，避免挡消球）
        self._core_started_at = time.monotonic()
        self._log_step("core_enter")

        t0 = time.monotonic()
        self._log_step("long_press_attack_start")
        self.action.long_press_attack(700)
        self._log_step("long_press_attack_done", elapsed_ms=int((time.monotonic() - t0) * 1000))

        self._log_step("burst_scheduled", next="p1_burst", ticks=_P1_CORE_BURST)
        self._begin_burst(_P1_CORE_BURST, "p1_burst")

    def _phase_p1_burst(self) -> None:
        # 优先消球1，再普攻
        tick = self._burst_ticks + 1
        self._log_step("burst_tick_enter", tick=f"{tick}/{self._burst_total}")

        t0 = time.monotonic()
        self._log_step("ball1_start", tick=f"{tick}/{self._burst_total}")
        self.action.ball_elimination_target(1)
        self._log_step("ball1_done", elapsed_ms=int((time.monotonic() - t0) * 1000))

        self._log_step("attack", tick=f"{tick}/{self._burst_total}")
        self.action.attack()

        t1 = time.monotonic()
        self._log_step("skill_start", tick=f"{tick}/{self._burst_total}")
        self.action.use_skill()
        self._log_step("skill_done", elapsed_ms=int((time.monotonic() - t1) * 1000))

        self._burst_ticks += 1
        if self._burst_ticks >= self._burst_total:
            self._log_step("burst_complete", ticks=self._burst_total)
            self.action.auxiliary_machine()
            self.action.use_qte()
            self.phase = "idle"

    def _phase_p2_farm(self) -> None:
        # 盲打窗口内不做识别；结束后查特球/长闪/球数
        self._p2_farm_burst()

        if self._red_ball_ready():
            self._enter_p2_ult(reason="p2_farm")
            return
        if self._try_p2_long_dodge():
            return
        if not self.action.count_signal_balls() or self._clear_expired():
            self.action.logger.info("希声2阶段 farm 结束 next=%s", self._p2_farm_next)
            if self._p2_farm_next == "switch":
                self.action.auxiliary_machine()
                self.action.use_skill_until_empty()
                self.action.auxiliary_machine()
                self.phase = "switch"
            else:
                self.phase = self._p2_farm_next

    def _phase_p2_core(self) -> None:
        if self._red_ball_ready():
            self._enter_p2_ult(reason="p2_core")
            return
        if self._try_p2_long_dodge():
            return
        # 2 阶段核心：长按后立即 burst
        self._core_started_at = time.monotonic()
        self._log_step("core_enter")

        t0 = time.monotonic()
        self._log_step("long_press_attack_start")
        self.action.long_press_attack(700)
        self._log_step("long_press_attack_done", elapsed_ms=int((time.monotonic() - t0) * 1000))

        self._log_step("burst_scheduled", next="p2_burst", ticks=_P2_CORE_BURST)
        self._begin_burst(_P2_CORE_BURST, "p2_burst")

    def _phase_p2_burst(self) -> None:
        # 每 tick 先查特球，命中则打断 burst 直接开大
        if self._red_ball_ready():
            self._enter_p2_ult(reason="p2_burst")
            return
        if self._try_p2_long_dodge():
            return

        tick = self._burst_ticks + 1
        self._log_step("burst_tick_enter", tick=f"{tick}/{self._burst_total}")

        t0 = time.monotonic()
        self._log_step("ball1_start", tick=f"{tick}/{self._burst_total}")
        self.action.ball_elimination_target(1)
        self._log_step("ball1_done", elapsed_ms=int((time.monotonic() - t0) * 1000))

        t1 = time.monotonic()
        self._log_step("ball2_start", tick=f"{tick}/{self._burst_total}")
        self.action.ball_elimination_target(2)
        self._log_step("ball2_done", elapsed_ms=int((time.monotonic() - t1) * 1000))

        self._log_step("attack", tick=f"{tick}/{self._burst_total}")
        self.action.attack()

        self._burst_ticks += 1
        if self._burst_ticks >= self._burst_total:
            self.action.logger.info("希声2阶段核心结束")
            self._log_step("burst_complete", ticks=self._burst_total)
            self._begin_p2_farm(next_after="switch")

    def _phase_p2_ult(self) -> None:
        self.action.use_skill_until_empty()
        self.action.auxiliary_machine()
        self.action.use_qte()
        self.phase = "switch"
