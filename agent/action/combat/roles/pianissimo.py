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
      └──2阶段──► p2_clear1 ──► p2_core ──► p2_burst ──► p2_clear2
                    │特球(红/黄)──► p2_ult ──► switch   （clear/burst 中亦可打断）
                    p2_clear2 ──无球──► p2_dodge ──► switch
"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

_PHASE2_NODE = "检查希声2阶段"
_RED_BALL_NODE = "检查希声红球"
_CLEAR_TIMEOUT = 10.0  # 消球阶段最长等待（秒）
_P1_BALL_MIN = 5  # 1 阶段开始消球所需最少信号球
_P1_CORE_BURST = 15  # 1 阶段核心后 burst 轮数（每轮 combat 循环 1 tick）
_P2_CORE_BURST = 20  # 2 阶段核心后 burst 轮数
_P1_FARM_MAX = 30  # 1 阶段攒球最多 tick，防止无限 farm
_FARM_TICK_MS = 50.0  # 攒球普攻间隔（毫秒）
_SWITCH_VERIFY_TIMEOUT = 15.0  # 希声切人动画较长，QTE 尝试窗口


class Pianissimo(BaseRole):
    """希声：1 阶段攒球消球开核心 → 2 阶段核心消球开大/长闪 → 切人。"""

    switch_verify_timeout = _SWITCH_VERIFY_TIMEOUT

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._clear_deadline = 0.0
        self._burst_ticks = 0
        self._burst_total = 0
        self._farm_ticks = 0
        self._next_farm_at = 0.0
        self._core_started_at = 0.0

    def reset_state(self) -> None:
        super().reset_state()
        self._clear_deadline = 0.0
        self._burst_ticks = 0
        self._burst_total = 0
        self._farm_ticks = 0
        self._next_farm_at = 0.0
        self._core_started_at = 0.0

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
        elif self.phase == "p2_clear1":
            self._phase_p2_clear1()
        elif self.phase == "p2_core":
            self._phase_p2_core()
        elif self.phase == "p2_burst":
            self._phase_p2_burst()
        elif self.phase == "p2_clear2":
            self._phase_p2_clear2()
        elif self.phase == "p2_ult":
            self._phase_p2_ult()
        elif self.phase == "p2_dodge":
            self._phase_p2_dodge()
        elif self.phase == "switch":
            self._phase_switch()
        else:
            self.phase = "idle"
            self._phase_idle()

    def _in_phase2(self) -> bool:
        return bool(self.action.check_status(_PHASE2_NODE))

    def _red_ball_ready(self) -> bool:
        return bool(self.action.check_status(_RED_BALL_NODE))

    def _enter_p2_ult(self, *, reason: str) -> None:
        """2 阶段检测到红/黄特球，进入开大 → 切人。"""
        self.action.logger.info("希声2阶段开大 (%s)", reason)
        self.phase = "p2_ult"

    def _begin_clear(self, *, next_phase: str) -> None:
        """进入消球阶段并启动超时计时。"""
        self._clear_deadline = time.monotonic() + _CLEAR_TIMEOUT
        self.phase = next_phase

    def _clear_expired(self) -> bool:
        return time.monotonic() >= self._clear_deadline

    def _begin_burst(self, total: int, next_after: str) -> None:
        """初始化 burst 计数并切换到 burst 阶段。"""
        self._burst_total = total
        self._burst_ticks = 0
        self.phase = next_after

    def _phase_idle(self) -> None:
        # 日常：锁视角普攻，按球数/阶段分流
        self.action.lens_lock()
        self.action.attack()

        if self._in_phase2():
            self.action.logger.info("希声2阶段")
            if self._red_ball_ready():
                self._enter_p2_ult(reason="idle")
                return
            self._begin_clear(next_phase="p2_clear1")
            return

        if self.action.count_signal_balls() > _P1_BALL_MIN:
            self.action.logger.info("希声1阶段")
            self._begin_clear(next_phase="p1_clear")
            return

        self.action.logger.info("希声1阶段信号球不足")
        self._farm_ticks = 0
        self._next_farm_at = 0.0
        self.phase = "p1_farm"

    def _phase_p1_farm(self) -> None:
        # 球不足时节流普攻攒球；未到 _next_farm_at 则本 tick 空转
        now = time.monotonic()
        if self._next_farm_at and now < self._next_farm_at:
            return

        tick_start = now
        if self._in_phase2() or self.action.count_signal_balls() > _P1_BALL_MIN:
            self.phase = "idle"
            return

        self.action.attack()
        self._farm_ticks += 1
        if self._farm_ticks >= _P1_FARM_MAX:
            self.phase = "idle"
            return

        elapsed_ms = (time.monotonic() - tick_start) * 1000
        wait_ms = max(0.0, _FARM_TICK_MS - elapsed_ms)
        self._next_farm_at = time.monotonic() + wait_ms / 1000

    def _phase_p1_clear(self) -> None:
        # 1 阶段消球；中途进 2 阶段则交 idle 重新分流
        if self._in_phase2():
            self.phase = "idle"
            return
        if not self.action.count_signal_balls() or self._clear_expired():
            self.action.logger.info("希声1阶段消球结束")
            self.phase = "p1_core"
            return

        self.action.attack()
        target = self.action.Arrange_Signal_Balls()
        self.action.attack()
        if target == -1:
            target = -2
        self.action.ball_elimination_target(target)
        self.action.logger.debug("希声1阶段消球 target=%s", target)
        self.action.attack()

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
        # 优先消球1，普攻用 post_attack 减截屏延迟
        tick = self._burst_ticks + 1
        self._log_step("burst_tick_enter", tick=f"{tick}/{self._burst_total}")

        t0 = time.monotonic()
        self._log_step("ball1_start", tick=f"{tick}/{self._burst_total}")
        self.action.ball_elimination_target(1)
        self._log_step("ball1_done", elapsed_ms=int((time.monotonic() - t0) * 1000))

        self._log_step("post_attack", tick=f"{tick}/{self._burst_total}")
        self.action.post_attack()

        t1 = time.monotonic()
        self._log_step("skill_start", tick=f"{tick}/{self._burst_total}")
        self.action.use_skill()
        self._log_step("skill_done", elapsed_ms=int((time.monotonic() - t1) * 1000))

        self._burst_ticks += 1
        if self._burst_ticks >= self._burst_total:
            self._log_step("burst_complete", ticks=self._burst_total)
            self.action.auxiliary_machine()
            self.action.auto_qte("a")
            self.phase = "idle"

    def _phase_p2_clear1(self) -> None:
        # 2 阶段首轮消球；见特球则直接开大
        if self._red_ball_ready():
            self._enter_p2_ult(reason="p2_clear1")
            return
        if not self.action.count_signal_balls() or self._clear_expired():
            self.action.logger.info("希声2阶段消球结束")
            self.phase = "p2_core"
            return

        self.action.ball_elimination_target(2)
        self.action.attack()

    def _phase_p2_core(self) -> None:
        if self._red_ball_ready():
            self._enter_p2_ult(reason="p2_core")
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

        self._log_step("post_attack", tick=f"{tick}/{self._burst_total}")
        self.action.post_attack()

        self._burst_ticks += 1
        if self._burst_ticks >= self._burst_total:
            self.action.logger.info("希声2阶段核心结束")
            self._log_step("burst_complete", ticks=self._burst_total)
            self.action.auto_qte("a")
            self._begin_clear(next_phase="p2_clear2")

    def _phase_p2_clear2(self) -> None:
        # burst 后再消一轮；见特球开大，无球则长闪收尾
        if self._red_ball_ready():
            self._enter_p2_ult(reason="p2_clear2")
            return
        if not self.action.count_signal_balls() or self._clear_expired():
            self.phase = "p2_dodge"
            return

        self.action.ball_elimination_target(2)
        self.action.attack()

    def _phase_p2_ult(self) -> None:
        # 红球大招 → 辅助机 → QTE → 切人
        self.action.use_skill()
        self.action.auxiliary_machine()
        self.action.auto_qte("a")
        self.phase = "switch"

    def _phase_p2_dodge(self) -> None:
        # 无红球时：长闪 + 辅助机/QTE + 技能，再切人
        self.action.long_press_dodge(700)
        self.action.auxiliary_machine()
        self.action.auto_qte("a")
        self.action.use_skill()
        self.action.auxiliary_machine()
        self.action.auto_qte("a")
        self.phase = "switch"

    def _phase_switch(self) -> None:
        # 2 阶段输出结束，请求切到下一位（受切人 CD 约束）
        if self.switch_next():
            self.action.logger.info("切换完成")
        self.phase = "idle"
