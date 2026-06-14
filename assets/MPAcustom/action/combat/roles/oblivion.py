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

from __future__ import annotations

import time

from MPAcustom.action.combat.core.role import BaseRole

class OblivionRole(BaseRole):
    def do_perform(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        if self.action.check_Skill_energy_bar():
            self.action.use_skill(1000)  # 技能
            self.action.auxiliary_machine()
            self.action.auto_qte("a")
            time.sleep(0.1)
            loop_count = 0
            while not self.action.check_Skill_energy_bar() and loop_count < 30:
                if self.combat.context.tasker.stopping:
                    return
                inside_item = 0
                self.action.attack()
                while (
                    self.action.count_signal_balls()
                    and inside_item < 5
                    and not self.action.check_Skill_energy_bar()
                ):
                    self.action.ball_elimination_target(1)
                    inside_item += 1
                    self.action.attack()
                    self.action.auto_qte("a")
                self.action.attack()
                if (
                    self.action.check_status("检查残月值_终焉")
                    and not self.action.check_Skill_energy_bar()
                ):
                    self.action.long_press_attack(2000)
                loop_count += 1
            self.action.use_skill(1000)  # 技能
            self.action.auxiliary_machine()
            self.action.auto_qte("a")
            for _ in range(10):
                self.action.attack()
            self.action.switch()
            print("切换完成")
            return
        else:
            for _ in range(30):
                if self.combat.context.tasker.stopping or self.action.check_Skill_energy_bar():
                    return
                item = 0
                self.action.attack()
                while self.action.count_signal_balls() and item < 5:
                    self.action.ball_elimination_target(1)
                    item += 1
                    self.action.attack()
                    self.action.auto_qte("a")
                self.action.attack()
                if self.action.check_status("检查残月值_终焉"):
                    self.action.long_press_attack(2000)
        self.action.attack()

        return
