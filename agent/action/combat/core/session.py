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
from action.combat.core.role_detect import (
    attack_templates_for_cls,
    detect_current_role,
    is_cls_on_field,
)
from action.combat.core.role_factory import ROLE_CLASS_MAP, create_role
from action.combat.core.switch import attempt_switch_to_color, blind_attack_click
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

    WAIT_COMBAT_TIME = 6.0
    SLEEP_CHECK_INTERVAL = 0.0
    WAIT_POLL_INTERVAL = 0.2
    COMBAT_UI_LOST_TIMEOUT = 8.0
    SWITCH_COOLDOWN = 15.0  # 离场后再上场 CD（每色位独立）
    FIELD_MIN_STAY = 5.0  # 上场后最少站场才可再切走（防抖）
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
        field_min_stay: float | None = None,
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
        self.field_min_stay = (
            field_min_stay if field_min_stay is not None else self.FIELD_MIN_STAY
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
        self._role_swap_cd_until: dict[str, float] = {}
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

    def _set_team_cls_at(self, color: str, cls_name: str) -> None:
        if self.team is None:
            return
        key = color.upper()
        if key == "R":
            self.team.R = cls_name
        elif key == "B":
            self.team.B = cls_name
        elif key == "Y":
            self.team.Y = cls_name

    def _rebind_role_at(self, color: str, cls_name: str) -> None:
        """按场上识别修正色位策略（roster 标 GeneralFight 但实际为专属角色等）。"""
        if self.team is None:
            return
        key = color.upper()
        old_cls = self.team.cls_at(key)
        role = self.roles.get(key)
        if old_cls == cls_name and role is not None and role.cls_name == cls_name:
            return
        if cls_name not in ROLE_CLASS_MAP:
            self.logger.warning("色位 %s 识别为未知策略 %s，保持 %s", key, cls_name, old_cls)
            return
        self.logger.info("色位 %s roster 修正: %s -> %s", key, old_cls, cls_name)
        self._set_team_cls_at(key, cls_name)
        self.roles[key] = create_role(self, key, cls_name)

    def _blind_attack_tick(self) -> None:
        """角色识别等阻塞流程中周期性盲发普攻。"""
        if self._should_stop():
            return
        blind_attack_click(self.context)

    def _correct_role_from_field(
        self, color: str, roster_cls: str, image: Any
    ) -> tuple[str, str]:
        """切人/进战后对照 attack_template，必要时将 GeneralFight 占位修正为专属 cls。"""
        self._blind_attack_tick()
        display_name, detected_cls = detect_current_role(
            self.context,
            image,
            on_tick=self._blind_attack_tick,
        )
        key = color.upper()

        if roster_cls == detected_cls:
            return display_name, roster_cls

        if roster_cls == "GeneralFight" and detected_cls not in ("GeneralFight",):
            self._rebind_role_at(key, detected_cls)
            return display_name, detected_cls

        if detected_cls not in ("GeneralFight",) and display_name != "未知":
            self.logger.warning(
                "色位 %s roster=%s 与场上 %s (%s) 不一致，按识别修正",
                key,
                roster_cls,
                display_name,
                detected_cls,
            )
            self._rebind_role_at(key, detected_cls)
            return display_name, detected_cls

        if display_name != "未知":
            return display_name, roster_cls
        return "未知", roster_cls

    def refresh_field_role_on_idle(self, role: BaseRole) -> bool:
        """
        idle 入口校验当前角色 attack_template；失配则重识别并更新 team.current。

        :return: True 表示已切换主站角色，本 tick 应跳过后续 idle 逻辑。
        """
        if self.team is None or self.team.is_solo():
            return False

        if not attack_templates_for_cls(role.cls_name):
            return False

        image = self.frame
        if image is None:
            return False

        if is_cls_on_field(self.context, image, role.cls_name):
            return False

        self._blind_attack_tick()
        display_name, detected_cls = detect_current_role(
            self.context,
            image,
            on_tick=self._blind_attack_tick,
        )
        if detected_cls == role.cls_name:
            return False

        cur = self.team.current.upper()
        if self.team.cls_at(cur) == role.cls_name and detected_cls != role.cls_name:
            if display_name != "未知":
                self.logger.info(
                    "idle 校验: 色位 %s roster=%s，识别为 %s (%s)，修正策略",
                    cur,
                    role.cls_name,
                    display_name,
                    detected_cls,
                )
                self._rebind_role_at(cur, detected_cls)
                self.current_role_name = display_name
                return True

        new_color: str | None = None
        for color in TEAM_COLORS:
            if self.team.cls_at(color) == detected_cls:
                new_color = color
                break

        if new_color is None:
            self.logger.warning(
                "idle 校验: 期望 %s 不在场，识别为 %s（不在 roster），保持当前",
                role.cls_name,
                detected_cls,
            )
            return False

        if new_color == self.team.current.upper():
            return False

        self.logger.info(
            "idle 校验: 期望 %s 不在场，重识别为 %s (%s) @%s",
            role.cls_name,
            display_name,
            detected_cls,
            new_color,
        )
        self.team.current = new_color
        self.current_role_name = display_name
        self.current_field_since = time.monotonic()
        target_role = self.roles.get(new_color)
        if target_role is not None:
            target_role.reset_state()
        return True

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

        image = self.frame
        if image is None:
            image = self.context.tasker.controller.post_screencap().wait().get()
        cur = self.team.current.upper()
        display_name, _ = self._correct_role_from_field(
            cur, self.team.cls_at(cur), image
        )
        if display_name != "未知":
            self.current_role_name = display_name

        self.current_field_since = time.monotonic()
        return True

    def get_current_role(self) -> BaseRole | None:
        if self.team is None:
            return None
        return self.roles.get(self.team.current.upper())

    def choose_switch_color(self, requester: BaseRole) -> str | None:
        """选切人目标色位；仅考虑当前可见 QTE 的 roster 色位。"""
        if self.team is None or self.team.is_solo():
            return None

        if self.SWITCH_STUB:
            others = self.team.other_filled_colors()
            return others[0] if others else None

        qte_colors = set(
            self.combat_check.detect_qte_colors(self.context, self)
        )
        now = time.monotonic()
        candidates: list[str] = []
        for color in self.team.other_filled_colors():
            if color not in qte_colors:
                continue
            cd_until = self._role_swap_cd_until.get(color, 0.0)
            if cd_until > now:
                role = self.roles.get(color)
                name = resolve_role_name(role.cls_name) if role else color
                self.logger.debug(
                    "切人目标 %s (%s) 再上场 CD 中剩余 %.1fs",
                    name,
                    color,
                    cd_until - now,
                )
                continue
            candidates.append(color)
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

    def request_role_switch(self, requester: BaseRole) -> bool:
        """切人统一入口：由 BaseRole.perform(switch) 或 switch_next() 调用。"""
        from_name = resolve_role_name(requester.cls_name)
        if self.is_switch_disabled():
            self.logger.info("切人跳过 [%s]: 切人已屏蔽", from_name)
            requester.on_switch_failed()
            return False
        if not self.can_switch():
            retry = self.switch_retry_cooldown_remaining()
            stay = self.field_stay_cooldown_remaining()
            if retry > 0:
                self.logger.info(
                    "切人跳过 [%s @%s]: 重试 CD 中剩余 %.1fs",
                    from_name,
                    requester.color,
                    retry,
                )
            elif stay > 0:
                self.logger.info(
                    "切人跳过 [%s @%s]: 站场 CD 中剩余 %.1fs",
                    from_name,
                    requester.color,
                    stay,
                )
            requester.on_switch_failed()
            return False

        target_color = self.choose_switch_color(requester)
        if not target_color:
            self.logger.info(
                "切人跳过 [%s @%s]: 无可用 QTE 目标",
                from_name,
                requester.color,
            )
            requester.on_switch_failed()
            return False

        target_cls = self.team.cls_at(target_color) if self.team else ""
        self.logger.info(
            "切人执行 [%s @%s] -> [%s @%s]",
            from_name,
            requester.color,
            resolve_role_name(target_cls),
            target_color,
        )
        if self.switch_to_color(target_color, attacker=requester):
            requester.reset_state()
            requester.on_switch_succeeded()
            return True

        requester.on_switch_failed()
        return False

    def is_switch_disabled(self) -> bool:
        return bool(self.SWITCH_DISABLED)

    def get_current_cls(self) -> str | None:
        if self.team is None:
            return None
        return self.team.current_cls()

    def can_switch(self) -> bool:
        """当前主站是否可发起切人（站场最短时长 + 失败重试 CD）。"""
        if self.SWITCH_STUB:
            return True
        if self.switch_retry_cooldown_remaining() > 0:
            return False
        return self.field_stay_cooldown_remaining() <= 0.0

    def switch_retry_cooldown_remaining(self) -> float:
        """切人失败后的重试 CD 剩余秒数。"""
        if self.last_switch_attempt_time <= 0 or self._switch_attempt_cooldown <= 0:
            return 0.0
        return max(
            0.0,
            self._switch_attempt_cooldown
            - (time.monotonic() - self.last_switch_attempt_time),
        )

    def field_stay_cooldown_remaining(self) -> float:
        """当前主站距可再切走剩余秒数（上场防抖）。"""
        if self.current_field_since <= 0:
            return 0.0
        elapsed = time.monotonic() - self.current_field_since
        return max(0.0, self.field_min_stay - elapsed)

    def role_reentry_cooldown_remaining(self, color: str) -> float:
        """指定色位离场后再切入的 CD 剩余秒数。"""
        cd_until = self._role_swap_cd_until.get(color.upper(), 0.0)
        return max(0.0, cd_until - time.monotonic())

    def role_swap_cooldown_remaining(self, color: str) -> float:
        """兼容旧名。"""
        return self.role_reentry_cooldown_remaining(color)

    def switch_cooldown_remaining(self) -> float:
        """当前主站发起切人的最大阻塞剩余秒数（站场 / 重试取较大）。"""
        return max(
            self.switch_retry_cooldown_remaining(),
            self.field_stay_cooldown_remaining(),
        )

    def switch_to_color(self, color: str, *, attacker: BaseRole | None = None) -> bool:
        """
        按色位切人：须先识别到目标 QTE，再盲发「攻击 + 换人」直到切换成功或超时。

        战前 roster 已写入 team；验证用 attack_template 比对目标色位 cls。
        CD 未好或 QTE 不可见 / 验证超时 → False，保持当前角色流程。
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
            if attacker is not None:
                self._role_swap_cd_until[attacker.color.upper()] = (
                    now + self.switch_cooldown
                )
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
            stay = self.field_stay_cooldown_remaining()
            retry = self.switch_retry_cooldown_remaining()
            if retry > 0:
                self.logger.info(
                    "切人重试 CD 中，剩余 %.1fs（当前 %s）",
                    retry,
                    self.team.current_cls(),
                )
            elif stay > 0:
                self.logger.info(
                    "站场 CD 中，剩余 %.1fs（当前 %s）",
                    stay,
                    self.team.current_cls(),
                )
            return False

        attacker_cb = (lambda: attacker.action.attack()) if attacker else None
        verify_timeout = self.SWITCH_VERIFY_TIMEOUT
        if attacker is not None and attacker.switch_verify_timeout is not None:
            verify_timeout = attacker.switch_verify_timeout
        switch_started = time.monotonic()
        if not attempt_switch_to_color(
            self.context,
            target,
            target_cls,
            attacker_callback=attacker_cb,
            verify_timeout=verify_timeout,
            poll_interval=self.SWITCH_VERIFY_POLL,
            should_stop=self._should_stop,
        ):
            elapsed = time.monotonic() - switch_started
            self.last_switch_attempt_time = time.monotonic()
            self._switch_attempt_cooldown = self.switch_fail_cooldown
            self.logger.info(
                "切人失败: %.1fs/%.1fs 内未切到 %s (%s)，继续当前角色（重试 CD %.0fs）",
                elapsed,
                verify_timeout,
                target,
                target_cls,
                self.switch_fail_cooldown,
            )
            return False

        now = time.monotonic()
        if attacker is not None:
            outgoing = attacker.color.upper()
            self._role_swap_cd_until[outgoing] = now + self.switch_cooldown
            self.logger.info(
                "再上场 CD: %s @%s %.0fs",
                resolve_role_name(attacker.cls_name),
                outgoing,
                self.switch_cooldown,
            )
        image = self.frame
        if image is None:
            image = self.context.tasker.controller.post_screencap().wait().get()
        display_name, target_cls = self._correct_role_from_field(
            target, self.team.cls_at(target), image
        )
        self.team.current = target
        self.current_field_since = now
        if display_name != "未知":
            self.current_role_name = display_name
        target_role = self.roles.get(target)
        if target_role is not None:
            target_role.reset_state()
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
        self._role_swap_cd_until = {}
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

        固定 overlay（重启等）→ in_combat → in_outer_interface → 8 秒丢失超时。
        """
        if self.combat_check.match_exit_overlay(self.context, self):
            return "outer_interface"

        if self.combat_check.in_combat(self.context, self):
            self.combat_ui_visible = True
            self._last_in_combat_time = time.monotonic()
            return ""

        self.combat_ui_visible = False

        if self.combat_check.in_outer_interface(self.context, self):
            return "outer_interface"

        lost_elapsed = time.monotonic() - self._last_in_combat_time
        if lost_elapsed >= self.combat_ui_lost_timeout:
            self.logger.info(
                "战斗 UI 未命中超时 (%.1f/%.1fs)",
                lost_elapsed,
                self.combat_ui_lost_timeout,
            )
            return "combat_ui_lost"
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
        on_tick = role.action.attack if role is not None else None
        active_delay(
            self.sleep_check_interval,
            on_tick=on_tick,
            should_stop=self._should_stop,
        )
