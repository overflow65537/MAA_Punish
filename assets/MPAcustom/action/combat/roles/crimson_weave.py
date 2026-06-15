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

from MPAcustom.action.combat.core.role import BaseRole


class CrimsonWeave(BaseRole):
    def do_perform(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        if self.action.get_hp_percent() >= 70:
            self.action.dodge()  # 闪避
            for _ in range(7):
                start_time = time.time()
                self.action.attack()
                light_less = self.action.check_status(
                    "检查无光值_囚影",
                )
                if light_less and light_less.best_result.text.isdigit():  # type: ignore
                    light_less_value = int(light_less.best_result.text)  # type: ignore
                else:
                    light_less_value = -1

                if light_less_value == -1:  # 处于一阶段
                    if self.action.check_Skill_energy_bar():
                        # 崩落的束缚化为利刃
                        for _ in range(10):
                            self.action.use_skill()
                            self.action.ball_elimination_target(1)
                            time.sleep(0.2)
                        self.action.auto_qte("a")
                        break
                elif (
                    light_less_value == 300 or light_less_value >= 474
                ):  # 无光值足够登龙
                    self.action.long_press_dodge(1500)
                    self.action.auto_qte("a")
                    self.action.long_press_attack(2300)  # 登龙
                    if self.action.check_Skill_energy_bar():
                        for _ in range(10):
                            self.action.use_skill()  # 宿命的囚笼由我斩断
                            time.sleep(0.2)
                        self.action.auxiliary_machine()
                    for _ in range(10):
                        self.action.ball_elimination_target(1)
                        time.sleep(0.2)
                    self.action.switch()
                    return
                elapsed = time.time() - start_time
                if elapsed < 0.3:
                    time.sleep(0.3 - elapsed)

        else:
            self.action.down_dodge()
            start_time = time.time()
            if not self.action.check_status(
                "检查无光值_囚影",
            ):  # 处于一阶段
                elapsed = time.time() - start_time
                if elapsed < 1.5:
                    time.sleep(1.5 - elapsed)
                self.action.up_dodge()
                if self.action.check_Skill_energy_bar():
                    # 崩落的束缚化为利刃
                    for _ in range(10):
                        self.action.use_skill()
                        self.action.ball_elimination_target(1)
                        time.sleep(0.2)
                    self.action.auxiliary_machine()

            else:
                elapsed = time.time() - start_time
                if elapsed < 1.5:
                    time.sleep(1.5 - elapsed)
                self.action.up_dodge()
                self.action.auto_qte("a")
                self.action.long_press_attack(2300)  # 登龙
                if self.action.check_Skill_energy_bar():
                    for _ in range(10):
                        self.action.use_skill()  # 宿命的囚笼由我斩断
                        time.sleep(0.2)
                    self.action.auxiliary_machine()
                for _ in range(10):
                    self.action.ball_elimination_target(1)
                    time.sleep(0.2)
                self.action.switch()
                print("切换角色")
        self.action.attack()

        return
