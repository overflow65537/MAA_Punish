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

"""幻奏战斗程序"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole


class Spectre(BaseRole):
    def do_perform(self) -> None:
        self.action.lens_lock()
        self.action.attack()
        if self.action.check_status("检查骇影2阶段"):
            print("二阶段")
            # 红球
            print("开始消红球")
            for _ in range(30):
                if self.action.check_status("检查骇影2阶段"):
                    self.action.ball_elimination_target(2)  # 消球
                    time.sleep(0.05)
                    self.action.ball_elimination_target(1)
                    time.sleep(0.05)
            time.sleep(0.1)
            self.action.auxiliary_machine()
            self.action.auto_qte("a")

            # 黄球
            print("开始消黄球")
            for _ in range(20):
                if self.action.check_status("检查骇影2阶段"):
                    self.action.attack()
                    time.sleep(0.05)
                    self.action.ball_elimination_target(1)
                    time.sleep(0.05)
            self.action.auxiliary_machine()
            self.action.auto_qte("a")

            # 蓝球
            print("开始消蓝球")
            self.action.long_press_attack(1000)
            for _ in range(10):
                if self.action.check_status("检查骇影2阶段"):
                    self.action.ball_elimination_target(1)
                    time.sleep(0.05)
                    self.action.attack()
                    time.sleep(0.05)

            self.action.auxiliary_machine()
            self.switch_next()
            print("切换完成")
            return
        elif self.action.count_signal_balls() >= 9:
            print("一阶段")
            item = 0
            while not self.action.check_Skill_energy_bar() and item < 100:
                self.action.ball_elimination_target(2)  # 消球
                time.sleep(0.05)
                self.action.ball_elimination_target(1)
                time.sleep(0.05)
                self.action.attack()
                time.sleep(0.05)
                item += 1

            self.action.use_skill()
            time.sleep(0.5)
        else:
            print("一阶段信号球不足")
            item = 0

            while not self.action.check_status("检查骇影2阶段") and item < 100:
                self.action.attack()
                print(bool(self.action.check_status("检查骇影2阶段")))
                time.sleep(0.05)
                item += 1
        self.action.attack()

        return
