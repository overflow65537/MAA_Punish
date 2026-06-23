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

"""澄心战斗程序"""

from __future__ import annotations

import time

from action.combat.core.role import BaseRole


class Limpidity(BaseRole):
    def do_perform(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        # 检查普攻1
        if self.action.check_status("检查普攻1_霁梦"):
            if self.action.check_status("检查核心条_霁梦"):
                self.action.long_press_dodge(1000)  # 直面天闪!
                self.action.auto_qte("a")
                print("直面天闪!")
                for _ in range(15):
                    self.action.use_skill()  # 以苦厄,澈我心镜
                    self.action.auxiliary_machine()
                    self.action.attack()
                    time.sleep(0.1)
                print("以苦厄,澈我心镜")
                self.action.attack()
                return
            # 信号球消除逻辑
            target = self.action.Arrange_Signal_Balls()
            if target > 0 or self.action.count_signal_balls() >= 5:
                self.action.ball_elimination_target(target)
                time.sleep(0.2)
                self.action.attack()
                return
        # 检查普攻2
        if self.action.check_status("检查普攻2_霁梦"):
            if self.action.check_status("检查核心球_霁梦"):
                start_time = time.time()
                while not self.action.check_status("检查核心条2_霁梦"):
                    if self.combat.context.tasker.stopping:
                        return
                    if time.time() - start_time > 5:
                        return
                    self.action.ball_elimination_target(1)  # 见证,我的意志
                    print("见证,我的意志")
                    time.sleep(0.1)
                self.action.auto_qte("a")

                self.action.long_press_attack(3000)  # 终于,梦醒时分
                print("终于,梦醒时分")
                for _ in range(15):
                    self.action.use_skill()  # 映天地,渡你新生
                    self.action.auxiliary_machine()
                    time.sleep(0.1)
                print("映天地,渡你新生")
                self.switch_next()
                print("切换完成")
                return
            elif self.action.count_signal_balls() != 0:
                self.action.ball_elimination_target()
                self.action.attack()
                return
        for _ in range(30):
            self.action.attack()
            time.sleep(0.1)

        return
