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

""" Piano 战斗程序"""

from __future__ import annotations

import time

from MPAcustom.action.combat.core.role import BaseRole


class Pianissimo(BaseRole):
    def do_perform(self) -> None:
        self.action.lens_lock()
        self.action.attack()
        if self.action.check_status("检查希声2阶段"):
            print("希声2阶段")
            start_time = time.time()

            while self.action.count_signal_balls() and time.time() - start_time < 10:
                if self.action.check_status("检查希声红球"):
                    self.action.use_skill()
                    return
                self.action.ball_elimination_target(2)
                time.sleep(0.05)
                self.action.attack()
                time.sleep(0.03)

            print("希声2阶段消球结束")

            self.action.long_press_attack(1000)
            self.action.auto_qte("a")
            for _ in range(20):
                self.action.attack()
                time.sleep(0.05)
                self.action.ball_elimination_target(1)
                self.action.ball_elimination_target(2)
                time.sleep(0.05)
            print("希声2阶段核心结束")

            start_time = time.time()
            while self.action.count_signal_balls() and time.time() - start_time < 10:
                if self.action.check_status("检查希声红球"):
                    self.action.use_skill()
                    time.sleep(0.2)
                    self.action.auxiliary_machine()
                    self.action.auto_qte("a")
                    self.switch_next()
                    print("切换完成")
                    return
                self.action.ball_elimination_target(2)
                time.sleep(0.05)
                self.action.attack()
                time.sleep(0.03)

            self.action.long_press_dodge(700)
            self.action.auxiliary_machine()
            self.action.auto_qte("a")

            for _ in range(5):
                time.sleep(0.05)
                self.action.use_skill()
                self.action.auxiliary_machine()
                self.action.auto_qte("a")
                self.switch_next()
                print("切换完成")
                return
        elif self.action.count_signal_balls() > 5:
            print("希声1阶段")
            start_time = time.time()
            while self.action.count_signal_balls() and time.time() - start_time < 10:
                if self.action.check_status("检查希声2阶段"):
                    return
                self.action.attack()
                target = self.action.Arrange_Signal_Balls()
                self.action.attack()
                if target == -1:
                    target = -2
                self.action.ball_elimination_target(target)
                time.sleep(0.05)
                print(target)
                self.action.attack()
                time.sleep(0.05)
            print("希声1阶段消球结束")

            self.action.long_press_attack(1000)
            time.sleep(0.01)
            self.action.auto_qte("a")
            self.action.auxiliary_machine()
            for _ in range(15):
                self.action.attack()
                time.sleep(0.05)
                self.action.ball_elimination_target(1)
                time.sleep(0.05)
                self.action.use_skill()
        else:
            print("希声1阶段信号球不足")
            for _ in range(30):
                start_time = time.time()
                if (
                    self.action.check_status("检查希声2阶段")
                    or self.action.count_signal_balls() > 5
                    or self.combat.context.tasker.stopping
                ):
                    break
                self.action.attack()
                end_time = time.time()
                elapsed_ms = (end_time - start_time) * 1000
                # 需要等待的时间（如果已用时间不足50ms）
                wait_ms = max(0, 50 - elapsed_ms)
                if wait_ms > 0:
                    time.sleep(wait_ms / 1000)
        self.action.attack()
        return
