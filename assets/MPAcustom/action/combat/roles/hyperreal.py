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

"""超刻战斗程序"""

from __future__ import annotations

import time

from MPAcustom.action.combat.core.role import BaseRole


class Hyperreal(BaseRole):
    def do_perform(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        if self.action.check_Skill_energy_bar():
            self.action.logger.info("大招就绪")
            self.action.use_skill()  # 在时间的尽头,湮灭吧
            self.action.auxiliary_machine()
            time.sleep(1)
            self.action.auto_qte("a")

        elif self.action.check_status("检查核心技能_超刻"):  # 核心技能就绪
            self.action.logger.info("核心技能就绪")
            self.action.long_press_attack()
            self.action.auto_qte("a")
            self.action.auxiliary_machine()

            start_time = time.time()
            while (
                not self.action.check_status("检查核心技能结束_超刻")
            ) and time.time() - start_time < 10:
                while self.action.count_signal_balls() and time.time() - start_time < 10:
                    self.action.ball_elimination_target(1)

                time.sleep(0.1)
                self.action.auto_qte("a")
                self.action.attack()
            self.action.logger.info("核心技能结束")
            self.action.auxiliary_machine()
            self.switch_next()
            print("切换完成")
            return
        else:
            self.action.logger.info("核心技能未就绪")
            self.action.continuous_attack(5, 100)
            target = self.action.Arrange_Signal_Balls("any")
            if self.action.count_signal_balls() >= 9 or target > 0:
                self.action.ball_elimination_target(target)
        self.action.attack()
        return
