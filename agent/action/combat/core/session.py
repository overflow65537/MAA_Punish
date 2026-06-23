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
MAA_Punish 战斗循环
作者:overflow65537
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from action.combat.core.provider import BaseCombatCheck
from action.combat.core.role import BaseRole, SwitchPriority, resolve_role_name
from action.combat.core.role_factory import create_role
from action.combat.core.switch import attempt_switch_to_color
from action.combat.core.team import TEAM_COLORS, TeamSnapshot
from action.combat.timing import active_delay
from action.combat.config.LoadSetting import ROLE_ACTIONS
from logger_component import LoggerComponent

if TYPE_CHECKING:
    from maa.context import Context


def _role_type_for_cls(cls_name: str) -> str:
    for role_info in ROLE_ACTIONS.values():
        if role_info.get("cls_name") == cls_name:
            return str(role_info.get("type", ""))
    return ""


class CombatTask:
    """战斗任务：进战 → 循环 perform → 退战。"""

    _ROLE_NOTIFY_NODE = (
        "发送消息_这是程序自动生成的node所以故意写的很长来防止某一天想不开用了这个名字导致报错"
    )

    WAIT_COMBAT_TIME = 30.0
    SLEEP_CHECK_INTERVAL = 0.0
    WAIT_POLL_INTERVAL = 0.2
    COMBAT_UI_LOST_TIMEOUT = 20.0
    SWITCH_COOLDOWN = 15.0
    SWITCH_FAIL_COOLDOWN = 2.0
    SWITCH_VERIFY_TIMEOUT = 12.0
    SWITCH_VERIFY_POLL = 0.05
    SWITCH_STUB = False
    SWITCH_DISABLED = False

    def __init__(
        self,
        context: Context,
        combat_check: BaseCombatCheck,
        *,
        wait_combat_time: float | None = None,
        sleep_check_interval: float | None = None,
        combat_ui_lost_timeout: float | None = None,
        switch_cooldown: float | None = None,
        switch_fail_cooldown: float | None = None,
    ):
        self.context = context
        self.combat_check = combat_check
        self.wait_combat_time = (
            wait_combat_time if wait_combat_time is not None else self.WAIT_COMBAT_TIME
        )
        self.sleep_check_interval = (
            sleep_check_interval
            if sleep_check_interval is not None
            else self.SLEEP_CHECK_INTERVAL
        )
        self.combat_ui_lost_timeout = (
            combat_ui_lost_timeout
            if combat_ui_lost_timeout is not None
            else self.COMBAT_UI_LOST_TIMEOUT
        )
        self.switch_cooldown = (
            switch_cooldown if switch_cooldown is not None else self.SWITCH_COOLDOWN
        )
        self.switch_fail_cooldown = (
            switch_fail_cooldown
            if switch_fail_cooldown is not None
            else self.SWITCH_FAIL_COOLDOWN
        )

        self._in_combat = False
        self.combat_ui_visible = False
        self.battle_state = "unknown"
        self.out_of_combat_reason = ""
        self.loop_count = 0
        self._last_in_combat_time = 0.0
        self.frame: Any | None = None

        self.team: TeamSnapshot | None = None
        self.roles: dict[str, BaseRole] = {}
        self.current_role_name: str = ""
        self.last_switch_attempt_time: float = 0.0
        self._switch_attempt_cooldown: float = 0.0
        self.current_field_since: float = 0.0

        self._logger_component = LoggerComponent(__name__)
        self.logger = self._logger_component.logger

    @property
    def combat_ui_lost_elapsed(self) -> float:
        """自上次识别到战斗 UI 以来经过的秒数。"""
        if not self._in_combat or self.combat_ui_visible:
            return 0.0
        return max(0.0, time.monotonic() - self._last_in_combat_time)

    def combat_once(self) -> None:
        """执行一次完整战斗流程。"""
        self.logger.info("战斗会话启动，等待进入战斗...")
        self._wait_in_combat()
        if not self._in_combat:
            return

        self._last_in_combat_time = time.monotonic()
        self.combat_ui_visible = True
        self.logger.info("进入战斗")

        if not self.load_team():
            self.out_of_combat_reason = "team_detect_failed"
            self.combat_end()
            return

        try:
            while self._in_combat:
                if self._should_stop():
                    self.out_of_combat_reason = "stopped"
                    break

                self._capture_frame()
                exit_reason = self._check_combat_presence()
                if exit_reason:
                    self.out_of_combat_reason = exit_reason
                    break

                self.perform()

                if self.combat_check.combat_end_condition(self.context, self):
                    self.out_of_combat_reason = "combat_end_condition"
                    break
                if not self.combat_check.on_combat_check(self.context, self):
                    self.out_of_combat_reason = "on_combat_check_failed"
                    break

                self.battle_state = self.combat_check.check_battle_state(
                    self.context, self
                )
                self._sleep_check()
        finally:
            self.combat_end()

    def perform(self) -> None:
        """dispatch 当前角色 do_perform。"""
        self.loop_count += 1
        role = self.get_current_role()
        if role is None:
            return
        if not self.combat_ui_visible:
            return
        if self._should_stop():
            return

        #self.logger.debug(
        #    "dispatch loop=%s cls=%s color=%s phase=%s switch=%s cd=%.1fs",
        #    self.loop_count,
        #    role.cls_name,
        #    role.color,
        #    role.phase,
        #    self.can_switch(),
        #    self.switch_cooldown_remaining(),
        #)
        role.perform()

    def load_team(self) -> bool:
        """进战识别当前角色，仅调用一次。"""
        snapshot = self.combat_check.detect_team(self.context, self)
        if snapshot is None:
            self.logger.warning("角色识别失败")
            return False

        self.team = snapshot
        self.roles = {}
        for color in TEAM_COLORS:
            cls_name = snapshot.cls_at(color)
            if cls_name:
                self.roles[color] = create_role(self, color, cls_name)
        for role in self.roles.values():
            role.reset_state()

        solo = "单人队" if snapshot.is_solo() else f"{len(snapshot.filled_colors())}人队"
        self.logger.info("识别到角色: %s (%s)", self.current_role_name, solo)
        self._notify_current_role()
        return True

    def _notify_current_role(self) -> None:
        """向 Pipeline focus 推送当前主站角色（兼容原 RecognitionRole 日志）。"""
        if not self.current_role_name:
            return
        try:
            self.context.override_pipeline(
                {
                    self._ROLE_NOTIFY_NODE: {
                        "focus": {
                            "Node.Recognition.Succeeded": (
                                f"识别到角色: {self.current_role_name}"
                            )
                        }
                    }
                }
            )
            self.context.run_task(self._ROLE_NOTIFY_NODE)
        except Exception:
            self.logger.debug("推送角色识别消息失败", exc_info=True)

    def get_current_role(self) -> BaseRole | None:
        if self.team is None:
            return None
        return self.roles.get(self.team.current.upper())

    def choose_switch_color(self, requester: BaseRole) -> str | None:
        """选切人目标色位。Phase 4 可扩展 buff 优先级。"""
        if self.team is None or self.team.is_solo():
            return None

        if self.SWITCH_STUB:
            others = self.team.other_filled_colors()
            return others[0] if others else None

        qte_colors = set(
            self.combat_check.detect_qte_colors(self.context, self)
        )
        candidates = [
            c for c in self.team.other_filled_colors() if c in qte_colors
        ]
        if not candidates:
            return None

        allowed: list[tuple[str, SwitchPriority, BaseRole]] = []
        for color in candidates:
            role = self.roles.get(color)
            if role is None:
                continue
            priority = role.get_switch_priority(requester)
            if priority != SwitchPriority.NO:
                allowed.append((color, priority, role))

        if not allowed:
            return None

        must_targets = [c for c, pri, _ in allowed if pri == SwitchPriority.MUST]
        if must_targets:
            return must_targets[0]

        requester_type = _role_type_for_cls(requester.cls_name)
        if requester_type == "Attacker":
            for prefer_type in ("Support", "Tank"):
                for color, _, role in allowed:
                    if _role_type_for_cls(role.cls_name) == prefer_type:
                        return color

        return allowed[self.loop_count % len(allowed)][0]

    def is_switch_enabled(self) -> bool:
        node = self.context.get_node_data("自动切换") or {}
        return bool(node.get("enabled", False))

    def is_switch_disabled(self) -> bool:
        return bool(self.SWITCH_DISABLED)

    def get_current_cls(self) -> str | None:
        if self.team is None:
            return None
        return self.team.current_cls()

    def can_switch(self) -> bool:
        if self.SWITCH_STUB:
            return True
        return self.switch_cooldown_remaining() <= 0.0

    def switch_cooldown_remaining(self) -> float:
        """距下次可切人剩余秒数（取「上次 QTE 尝试」与「当前角色上场」两者较大值）。"""
        now = time.monotonic()
        remainders: list[float] = []
        if self.last_switch_attempt_time > 0 and self._switch_attempt_cooldown > 0:
            remainders.append(
                self._switch_attempt_cooldown
                - (now - self.last_switch_attempt_time)
            )
        if self.current_field_since > 0:
            remainders.append(
                self.switch_cooldown - (now - self.current_field_since)
            )
        if not remainders:
            return 0.0
        return max(0.0, max(remainders))

    def switch_to_color(self, color: str, *, attacker: BaseRole | None = None) -> bool:
        """
        按色位切人：SWITCH_VERIFY_TIMEOUT 内持续单击攻击并点击目标 QTE，直到识别到切换。

        战前 roster 已写入 team；验证用 attack_template 比对目标色位 cls。
        CD 未好或验证超时仍未切换 → False，保持当前角色流程。
        """
        if self.SWITCH_DISABLED:
            self.logger.debug("切人已暂时屏蔽")
            return False

        if self.team is None:
            return False

        target = color.upper()
        if target not in TEAM_COLORS:
            self.logger.warning("无效切人色位: %s", color)
            return False

        if target == self.team.current.upper():
            return False

        target_cls = self.team.cls_at(target)
        if not target_cls:
            self.logger.debug("色位 %s 无人，跳过切人", target)
            return False

        if self.SWITCH_STUB:
            self.team.current = target
            now = time.monotonic()
            self.last_switch_attempt_time = now
            self._switch_attempt_cooldown = self.switch_cooldown
            self.current_field_since = now
            target_role = self.roles.get(target)
            if target_role is not None:
                target_role.reset_state()
            self.logger.info(
                "切人 stub -> %s (%s)",
                target,
                self.team.current_cls(),
            )
            return True

        if not self.can_switch():
            self.logger.info(
                "切人 CD 中，剩余 %.1fs（当前 %s）",
                self.switch_cooldown_remaining(),
                self.team.current_cls(),
            )
            return False

        attacker_cb = (lambda: attacker.action.click_attack()) if attacker else None
        verify_timeout = self.SWITCH_VERIFY_TIMEOUT
        if attacker is not None and attacker.switch_verify_timeout is not None:
            verify_timeout = attacker.switch_verify_timeout
        if not attempt_switch_to_color(
            self.context,
            target,
            target_cls,
            attacker_callback=attacker_cb,
            verify_timeout=verify_timeout,
            poll_interval=self.SWITCH_VERIFY_POLL,
            should_stop=self._should_stop,
        ):
            self.last_switch_attempt_time = time.monotonic()
            self._switch_attempt_cooldown = self.switch_fail_cooldown
            self.logger.info(
                "切人失败: %.1fs 内持续点击仍未切到 %s (%s)，继续当前角色（重试 CD %.0fs）",
                verify_timeout,
                target,
                target_cls,
                self.switch_fail_cooldown,
            )
            return False

        now = time.monotonic()
        self.last_switch_attempt_time = now
        self._switch_attempt_cooldown = self.switch_cooldown
        self.team.current = target
        self.current_field_since = now
        self.current_role_name = resolve_role_name(target_cls)
        target_role = self.roles.get(target)
        if target_role is not None:
            target_role.reset_state()
        self._notify_current_role()
        self.logger.info(
            "切人成功 -> %s (%s)",
            target,
            self.team.current_cls(),
        )
        return True

    def combat_end(self) -> None:
        """战斗结束清理。"""
        self._in_combat = False
        self.combat_ui_visible = False
        self.frame = None
        self.team = None
        self.roles = {}
        self.current_role_name = ""
        self.last_switch_attempt_time = 0.0
        self._switch_attempt_cooldown = 0.0
        self.current_field_since = 0.0
        reason = self.out_of_combat_reason or "unknown"
        self.logger.info("战斗结束: %s", reason)

    def _capture_frame(self) -> Any:
        """每轮循环截屏一次，供 in_combat / in_outer_interface 等复用。"""
        self.frame = self.context.tasker.controller.post_screencap().wait().get()
        return self.frame

    def _check_combat_presence(self) -> str:
        """
        更新战斗 UI 可见状态并判断是否应退战。

        优先 in_combat（快路径）：命中则立即继续，跳过外部界面检查。
        未命中时再查 in_outer_interface，最后才计 20 秒丢失超时。
        """
        if self.combat_check.in_combat(self.context, self):
            self.combat_ui_visible = True
            self._last_in_combat_time = time.monotonic()
            return ""

        self.combat_ui_visible = False

        if self.combat_check.in_outer_interface(self.context, self):
            return "outer_interface"

        lost_elapsed = time.monotonic() - self._last_in_combat_time
        if lost_elapsed >= self.combat_ui_lost_timeout:
            return "combat_ui_lost"

        self.logger.debug(
            "战斗 UI 未命中，继续战斗 (%.1f/%.1fs)",
            lost_elapsed,
            self.combat_ui_lost_timeout,
        )
        return ""

    def _wait_in_combat(self) -> None:
        deadline = time.monotonic() + self.wait_combat_time
        while time.monotonic() < deadline:
            if self._should_stop():
                self.out_of_combat_reason = "stopped"
                return
            self._capture_frame()
            if self.combat_check.in_combat(self.context, self):
                self._in_combat = True
                return
            time.sleep(self.WAIT_POLL_INTERVAL)

        self.logger.info("等待进入战斗超时")
        self.out_of_combat_reason = "enter_timeout"

    def _should_stop(self) -> bool:
        return bool(self.context.tasker.stopping)

    def _sleep_check(self) -> None:
        if self._should_stop() or self.sleep_check_interval <= 0:
            return
        role = self.get_current_role()
        on_tick = role.action.post_attack if role is not None else None
        active_delay(
            self.sleep_check_interval,
            on_tick=on_tick,
            should_stop=self._should_stop,
        )
