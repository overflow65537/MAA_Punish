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

"""深红囚影战斗程序（小太刀 ↔ 大太刀状态机，高血流程）"""

from __future__ import annotations

import time

from MPAcustom.action.combat.core.role import BaseRole

# Pipeline: Auto_Battle/Check_Characters_Skill/
#   Common.jsonc / 囚影.jsonc 等
#   检查大太刀无光值     → 颜色 + 文本 And，判定大太刀形态
#   检查大太刀无光值_文本 → OCR 读数 (0~600)，登龙阈值用
#   检查小太刀无光值     → 颜色 + 文本 And，判定小太刀形态
_GREAT_LIGHT_NODE = "检查大太刀无光值"
_GREAT_LIGHT_TEXT_NODE = "检查大太刀无光值_文本"
_SMALL_LIGHT_NODE = "检查小太刀无光值"
_SMALL_LIGHT_TEXT_NODE = "检查小太刀无光值_文本"
# 闪避后特殊连段窗口（Check_Characters_Skill/囚影.jsonc）
_SMALL_SPECIAL_NODE = "检查小太刀特殊攻击"
_GREAT_SPECIAL_NODE = "检查大太刀特殊攻击"
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


class CrimsonWeave(BaseRole):
    """囚影：小太刀 ↔ 大太刀循环（双无光条 OCR 判定形态）。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ult_wait_deadline = 0.0
        self._great_special_locked = False
        self._special_boot = False
        self._special_saw_bar = False
        self._dragon_charge_deadline = 0.0
        self._dragon_red_deadline = 0.0
        self._dragon_start_blocked_until = 0.0
        self._sword_probe_cache: tuple[str | None, int | None, int | None] | None = None

    def reset_state(self) -> None:
        super().reset_state()
        self._ult_wait_deadline = 0.0
        self._great_special_locked = False
        self._special_boot = False
        self._special_saw_bar = False
        self._dragon_charge_deadline = 0.0
        self._dragon_red_deadline = 0.0
        self._dragon_start_blocked_until = 0.0
        self._sword_probe_cache = None

    def do_perform(self) -> None:
        if self.combat.context.tasker.stopping:
            return

        self._sword_probe_cache = None

        # 大太刀最高优先级：无光值达标 → 登龙充能；红色无光 → 长按攻击登龙
        if self.phase not in _PHASES_SKIP_DRAGON_PRIORITY and self._try_dragon_now():
            return

        # 小太刀最高优先级：大招能量满 → 立即停止一切，释放大招
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

    def _clear_special_combo_state(self) -> None:
        self._great_special_locked = False
        self._special_boot = False
        self._special_saw_bar = False

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
            self._clear_special_combo_state()
            self._dragon_red_deadline = time.monotonic() + _DRAGON_RED_WAIT_TIMEOUT
            self.phase = "great_dragon_red"
            self._phase_great_dragon_red()
            return True

        if great_light is None or not self._light_ready_for_dragon(great_light):
            return False

        self.action.logger.info("无光值达标(%s)，开始登龙充能", great_light)
        self._clear_special_combo_state()
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
            self.action.logger.info("登龙后大招就绪")
            self.phase = "great_ult"
        else:
            self.phase = "great_ball"

    def _cast_ult_if_ready(self) -> bool:
        """大招条就绪则点大招；宁可误点也不漏点。"""
        if not self.action.check_Skill_energy_bar():
            return False
        self.action.use_skill()
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
        self._clear_special_combo_state()
        self.phase = "small_dodge"
        return True

    def _begin_special_combo_after_dodge(self) -> None:
        """闪避后下一 tick 点攻击启动特殊连段。"""
        self._special_boot = True
        self._special_saw_bar = False

    def _tick_special_combo(self, special_node: str) -> bool:
        """
        闪避后首击启动 → 特殊条在则持续攻击 → 条消失则结束。
        条未出现时闪避+攻击唤条（不再只普攻干等）。
        返回 True 表示连段仍在进行。
        """
        if self.action.check_status(special_node):
            self._special_saw_bar = True
            self._special_boot = False
            self.action.attack()
            return True

        if self._special_saw_bar:
            self._special_saw_bar = False
            return False

        if self._special_boot:
            self.action.attack()
            self._special_boot = False
            return True

        self.action.logger.info("特殊条未识别，闪避+攻击唤条")
        self.action.dodge()
        self.action.attack()
        return True

    def _phase_idle(self) -> None:
        self.action.lens_lock()
        self.phase = "small_dodge"

    def _phase_small_dodge(self) -> None:
        self.action.dodge()
        self._begin_special_combo_after_dodge()
        self.phase = "small_attack"

    def _phase_small_attack(self) -> None:
        mode, great_light, _ = self._probe_sword_mode()
        if mode == "great":
            self.action.logger.info(
                "检测到大太刀无光值=%s，转入大太刀流程", great_light
            )
            self.phase = "great_ball"
            return

        if self._tick_special_combo(_SMALL_SPECIAL_NODE):
            return

        self.phase = "small_dodge"

    def _phase_small_ult(self) -> None:
        """小太刀开大 → 进入大太刀；能量条在就持续点大招。"""
        if self._cast_ult_if_ready():
            return

        self.action.auto_qte("a")
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
            self.phase = "small_attack"
            return

        if self._cast_ult_if_ready():
            return

        self.action.ball_elimination_target(1)

    def _phase_great_ball(self) -> None:
        """大太刀：有球则固定消 1 号球攒无光/大招；无球则闪避连段攒球。"""
        if self._maybe_leave_great_sword():
            return

        if self.action.count_signal_balls() > 0:
            self.action.ball_elimination_target(1)
        else:
            self.phase = "great_build_dodge"

    def _phase_great_build_dodge(self) -> None:
        if self._maybe_leave_great_sword():
            return

        self.action.dodge()
        self._begin_special_combo_after_dodge()
        self._great_special_locked = True
        self.phase = "great_build_attack"

    def _phase_great_build_attack(self) -> None:
        if self._maybe_leave_great_sword():
            return

        if self._great_special_locked:
            if self._tick_special_combo(_GREAT_SPECIAL_NODE):
                return
            self._great_special_locked = False

        if self.action.count_signal_balls() > 0:
            self.phase = "great_ball"
            return

        self.phase = "great_build_dodge"

    def _phase_great_ult(self) -> None:
        """大太刀大招；能量条在就持续点大招。"""
        if self._cast_ult_if_ready():
            return

        self.action.auxiliary_machine()
        self.action.auto_qte("a")
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
