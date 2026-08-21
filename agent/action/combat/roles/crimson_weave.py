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

"""深红囚影战斗程序"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole

# Pipeline: Auto_Battle/Check_Characters_Skill/
#   Common.jsonc / 囚影.jsonc 等
#   检查大太刀无光值     → 颜色 + 文本 And，判定大太刀形态
#   检查大太刀无光值_文本 → OCR 读数 (0~600)，登龙阈值用
#   检查小太刀无光值     → 颜色 + 文本 And，判定小太刀形态
_GREAT_LIGHT_NODE = "检查大太刀无光值"
_GREAT_LIGHT_TEXT_NODE = "检查大太刀无光值_文本"
_SMALL_LIGHT_NODE = "检查小太刀无光值"
_SMALL_LIGHT_TEXT_NODE = "检查小太刀无光值_文本"
# 闪避起算，连续点普攻（大小太刀相同，不识别特殊条；大招可打断）
_DODGE_ATTACK_S = 2.0
# 登龙：无光 OCR 达标后按下闪避充能 → 松开 → 红色无光 → 长按攻击
_LIGHT_DRAGON_EXACT = 300
_LIGHT_DRAGON_MIN = 474
_DRAGON_CHARGE_FULL_NODE = "检查登龙充能满"
_DRAGON_RED_LIGHT_NODE = "检查登龙红色无光值"
_DRAGON_CHARGE_TIMEOUT = 3.0
_DRAGON_RED_WAIT_TIMEOUT = 5.0
# 小太刀开大落地后大太刀会闪 600 但不可操作，短暂禁止发起登龙
_DRAGON_START_BLOCK = 2.0
_DRAGON_PHASES = frozenset(
    {"great_dragon_press", "great_dragon_charge", "great_dragon_red"}
)
_ULT_WAIT_TIMEOUT = 12.0
# 实测落地→无光 OCR 约 0.4s，在此基础上再加缓冲；超时内每 tick 盲消 1 号球
_SMALL_ULT_LAND_DELAY = 0.5
_SMALL_ULT_WAIT_EXTRA = 3.0
_SMALL_ULT_WAIT_TIMEOUT = _SMALL_ULT_LAND_DELAY + _SMALL_ULT_WAIT_EXTRA

# 这些阶段不抢登龙（小太刀/大太刀开大动画中、正在登龙）
_PHASES_SKIP_DRAGON_PRIORITY = (
    frozenset(
        {
            "idle",
            "small_dodge",
            "small_ult",
            "small_ult_wait",
            "great_ult",
            "great_ult_wait",
        }
    )
    | _DRAGON_PHASES
)
# 这些阶段不抢小太刀大招（已在开大或等大太刀/小太刀切换）
_PHASES_SKIP_SMALL_ULT_PRIORITY = frozenset(
    {"small_ult", "small_ult_wait", "great_ult", "great_ult_wait"}
)
# 先点普攻再识别，避免大招落地/消球后空等（多半会进闪避普攻连段）
_PHASES_ATTACK_WHILE_PROBE = frozenset(
    {
        "small_dodge",
        "small_attack",
        "small_ult_wait",
        "great_ball",
        "great_build_dodge",
        "great_build_attack",
        "great_ult_wait",
    }
)


class CrimsonWeave(BaseRole):
    """囚影：小太刀 ↔ 大太刀循环（双无光条 OCR 判定形态）。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ult_wait_deadline = 0.0
        self._dragon_charge_deadline = 0.0
        self._dragon_red_deadline = 0.0
        self._dragon_start_blocked_until = 0.0
        self._sword_probe_cache: tuple[str | None, int | None, int | None] | None = None

    def reset_state(self) -> None:
        super().reset_state()
        self._ult_wait_deadline = 0.0
        self._dragon_charge_deadline = 0.0
        self._dragon_red_deadline = 0.0
        self._dragon_start_blocked_until = 0.0
        self._sword_probe_cache = None

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        self._sword_probe_cache = None

        if self.phase in _PHASES_ATTACK_WHILE_PROBE:
            self._tap_attack()

        # 大太刀最高优先级：无光值达标 → 登龙充能；红色无光 → 长按攻击登龙
        if self.phase not in _PHASES_SKIP_DRAGON_PRIORITY and self._try_dragon_now():
            return

        # 小太刀大招能量满 → 立即停止当前动作（登龙仍优先于大招；大太刀大招不抢连段）
        if (
            self.phase not in _PHASES_SKIP_SMALL_ULT_PRIORITY
            and self._try_small_ult_now()
        ):
            return

        if self.phase == "idle":
            self._phase_idle()
        elif self.phase == "small_dodge":
            self._phase_small_dodge()
        elif self.phase == "small_attack":
            self._phase_small_attack()
        elif self.phase == "small_ult":
            self._phase_small_ult()
        elif self.phase == "small_ult_wait":
            self._phase_small_ult_wait()
        elif self.phase == "great_ball":
            self._phase_great_ball()
        elif self.phase == "great_build_dodge":
            self._phase_great_build_dodge()
        elif self.phase == "great_build_attack":
            self._phase_great_build_attack()
        elif self.phase == "great_dragon_press":
            self._phase_great_dragon_press()
        elif self.phase == "great_dragon_charge":
            self._phase_great_dragon_charge()
        elif self.phase == "great_dragon_red":
            self._phase_great_dragon_red()
        elif self.phase == "great_ult":
            self._phase_great_ult()
        elif self.phase == "great_ult_wait":
            self._phase_great_ult_wait()
        else:
            self._phase_idle()

    def _light_bar_present(self, node: str) -> bool:
        """And/识别节点命中 → 无光条在场。"""
        return bool(self.action.check_status(node))

    def _read_light_text(self, text_node: str) -> int | None:
        """OCR 文本节点 → 读数（含 0）；未命中 → None。"""
        result = self.action.check_status(text_node)
        if not result:
            return None
        text = str(getattr(result.best_result, "text", "")).strip()  # type: ignore[union-attr]
        if text.isdigit():
            return int(text)
        return 0

    def _probe_sword_mode(
        self,
    ) -> tuple[str | None, int | None, int | None]:
        """探测形态：great / small / None(转换中或未识别)。同一 tick 内缓存。"""
        if self._sword_probe_cache is not None:
            return self._sword_probe_cache

        great_hit = self._light_bar_present(_GREAT_LIGHT_NODE)
        if self.phase in _PHASES_ATTACK_WHILE_PROBE:
            self._tap_attack()
        small_hit = self._light_bar_present(_SMALL_LIGHT_NODE)
        great_light = (
            self._read_light_text(_GREAT_LIGHT_TEXT_NODE) if great_hit else None
        )
        small_light = (
            self._read_light_text(_SMALL_LIGHT_TEXT_NODE) if small_hit else None
        )
        if great_hit and great_light is None:
            great_light = 0

        if great_hit and small_hit:
            self.action.logger.warning(
                "大小太刀无光条同时命中(大=%s,小=%s)，优先大太刀",
                great_light,
                small_light,
            )
            mode: str | None = "great"
        elif great_hit:
            mode = "great"
        elif small_hit:
            mode = "small"
        else:
            mode = None

        self._sword_probe_cache = (mode, great_light, small_light)
        return self._sword_probe_cache

    def _is_great_sword(self) -> bool:
        return self._probe_sword_mode()[0] == "great"

    def _is_small_sword(self) -> bool:
        return self._probe_sword_mode()[0] == "small"

    def _read_great_light(self) -> int | None:
        mode, great_light, _ = self._probe_sword_mode()
        if mode != "great":
            return None
        return great_light

    def _light_ready_for_dragon(self, value: int) -> bool:
        return value == _LIGHT_DRAGON_EXACT or value >= _LIGHT_DRAGON_MIN

    def _dragon_red_ready(self) -> bool:
        return bool(self.action.check_status(_DRAGON_RED_LIGHT_NODE))

    def _try_dragon_now(self) -> bool:
        """无光值达标 → 进入登龙充能；红色无光已现 → 直接长按攻击登龙。"""
        if self.phase in _DRAGON_PHASES:
            return False

        if time.monotonic() < self._dragon_start_blocked_until:
            return False

        mode, great_light, _ = self._probe_sword_mode()
        if mode != "great":
            return False

        if self._dragon_red_ready():
            self.action.logger.info("检测到登龙红色无光，长按攻击登龙")
            self._dragon_red_deadline = time.monotonic() + _DRAGON_RED_WAIT_TIMEOUT
            self.phase = "great_dragon_red"
            self._phase_great_dragon_red()
            return True

        if great_light is None or not self._light_ready_for_dragon(great_light):
            return False

        self.action.logger.info("无光值达标(%s)，开始登龙充能", great_light)
        self.phase = "great_dragon_press"
        self._phase_great_dragon_press()
        return True

    def _phase_great_dragon_press(self) -> None:
        self.action.down_dodge()
        self._dragon_charge_deadline = time.monotonic() + _DRAGON_CHARGE_TIMEOUT
        self.phase = "great_dragon_charge"

    def _phase_great_dragon_charge(self) -> None:
        if self.action.check_status(_DRAGON_CHARGE_FULL_NODE):
            self.action.up_dodge()
            self._dragon_red_deadline = time.monotonic() + _DRAGON_RED_WAIT_TIMEOUT
            self.phase = "great_dragon_red"
            self.action.logger.info("登龙充能满，松开闪避等待红色无光")
            return

        if time.monotonic() >= self._dragon_charge_deadline:
            self.action.up_dodge()
            self.action.logger.warning("登龙充能超时，放弃登龙")
            self.phase = "great_ball"

    def _phase_great_dragon_red(self) -> None:
        if not self._dragon_red_ready():
            if time.monotonic() >= self._dragon_red_deadline:
                self.action.logger.warning("等待登龙红色无光超时，放弃登龙")
                self.phase = "great_ball"
            return

        self.action.long_press_attack(2300)
        self.action.logger.info("登龙完成")

        if self.action.check_Skill_energy_bar():
            self.action.use_skill_until_empty()
            self.action.auxiliary_machine()

        for _ in range(10):
            self.action.ball_elimination_target(1)
            time.sleep(0.02)

        if self.switch_next():
            return

        if self.action.check_Skill_energy_bar():
            self.action.logger.info("登龙后大招就绪")
            self.phase = "great_ult"
        else:
            self.phase = "great_ball"

    def _cast_ult_if_ready(self) -> bool:
        """大招条就绪则连放至能量空。"""
        if not self.action.check_Skill_energy_bar():
            return False
        self.action.use_skill_until_empty()
        return True

    def _try_small_ult_now(self) -> bool:
        """小太刀大招就绪则立即释放并消费本 tick。返回 True 表示已进入/继续开大。"""
        if self._is_great_sword():
            return False
        if not self.action.check_Skill_energy_bar():
            return False
        if self.phase != "small_ult":
            self.action.logger.info("小太刀大招就绪，立即释放")
            self.phase = "small_ult"
        self._phase_small_ult()
        return True

    def _maybe_leave_great_sword(self) -> bool:
        """明确识别到小太刀 → 切回小太刀。未命中时不误判。"""
        if not self._is_small_sword():
            return False
        self.action.logger.info("识别到小太刀")
        self.phase = "small_dodge"
        return True

    def _tap_attack(self) -> None:
        """识别空档补一刀：只点攻击键，不截屏、不自动闪避。"""
        self.action.context.run_action("攻击")

    def _dodge_then_attack(self) -> bool:
        """闪避起算，两秒内持续点普攻。仅小太刀大招能量满时中断；大太刀不抢。

        Returns:
            True: 小太刀且能量条就绪，调用方应马上开大；False: 打满两秒或任务停止。
        """
        deadline = time.monotonic() + _DODGE_ATTACK_S
        self.action.dodge()
        while time.monotonic() < deadline:
            if self.combat.context.tasker.stopping:
                return False
            if self._is_small_sword() and self.action.check_Skill_energy_bar(
                fresh=True
            ):
                return True
            self.action.attack()
        return False

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.phase = "small_dodge"

    def _phase_small_dodge(self) -> None:
        if self._dodge_then_attack():
            self.action.logger.info("小太刀大招就绪，打断持续攻击")
            self.phase = "small_ult"
            self._phase_small_ult()
            return
        self.phase = "small_attack"

    def _phase_small_attack(self) -> None:
        mode, great_light, _ = self._probe_sword_mode()
        if mode == "great":
            self.action.logger.info(
                "检测到大太刀无光值=%s，转入大太刀流程", great_light
            )
            self.phase = "great_ball"
            self._phase_great_ball()
            return

        self.phase = "small_dodge"
        self._phase_small_dodge()

    def _phase_small_ult(self) -> None:
        """小太刀开大 → 进入大太刀；能量条在就持续点大招。"""
        if self._cast_ult_if_ready():
            return

        self.action.auxiliary_machine()
        self.action.use_qte()
        self._ult_wait_deadline = time.monotonic() + _SMALL_ULT_WAIT_TIMEOUT
        self.phase = "small_ult_wait"
        self.action.logger.info("小太刀大招释放完毕，等待大太刀无光值出现")

    def _phase_small_ult_wait(self) -> None:
        # 明确识别到大太刀 → 转入消球；否则盲消 + 补点大招
        mode, great_light, _ = self._probe_sword_mode()
        if mode == "great":
            self.action.logger.info("大太刀就绪，无光值=%s", great_light)
            self._dragon_start_blocked_until = time.monotonic() + _DRAGON_START_BLOCK
            self.phase = "great_ball"
            return

        if time.monotonic() >= self._ult_wait_deadline:
            self.action.logger.warning("等待大太刀无光值超时，回到小太刀攻击")
            self.phase = "small_dodge"
            return

        if self._cast_ult_if_ready():
            return

        self.action.ball_elimination_target(1)

    def _phase_great_ball(self) -> None:
        """大太刀：有球则固定消 1 号球攒无光/大招；无球则闪避连段攒球。"""
        if self._maybe_leave_great_sword():
            self._phase_small_dodge()
            return

        if self.action.count_signal_balls() > 0:
            self.action.ball_elimination_target(1)
            return

        self.phase = "great_build_dodge"
        self._phase_great_build_dodge()

    def _phase_great_build_dodge(self) -> None:
        if self._maybe_leave_great_sword():
            self._phase_small_dodge()
            return

        if self._dodge_then_attack():
            self.action.logger.info("小太刀大招就绪，打断持续攻击")
            self.phase = "small_ult"
            self._phase_small_ult()
            return
        self.phase = "great_build_attack"

    def _phase_great_build_attack(self) -> None:
        if self._maybe_leave_great_sword():
            self._phase_small_dodge()
            return

        if self.action.count_signal_balls() > 0:
            self.phase = "great_ball"
            self._phase_great_ball()
            return

        self.phase = "great_build_dodge"
        self._phase_great_build_dodge()

    def _phase_great_ult(self) -> None:
        """大太刀大招；能量条在就持续点大招。"""
        if self._cast_ult_if_ready():
            return

        self.action.auxiliary_machine()
        self.action.use_qte()
        self._ult_wait_deadline = time.monotonic() + _ULT_WAIT_TIMEOUT
        self.phase = "great_ult_wait"
        self.action.logger.info("大太刀大招释放完毕，等待回到小太刀")

    def _phase_great_ult_wait(self) -> None:
        if self._is_small_sword():
            self.action.logger.info("已回到小太刀")
            self.phase = "small_dodge"
            return

        if time.monotonic() >= self._ult_wait_deadline:
            self.action.logger.warning("等待回到小太刀超时，继续大太刀")
            self.phase = "great_ball"
            return

        if self._cast_ult_if_ready():
            return

        self.action.attack()
