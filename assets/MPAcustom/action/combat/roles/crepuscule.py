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

"""深痕战斗程序"""

from __future__ import annotations

import time

from MPAcustom.action.combat.core.role import BaseRole


class Crepuscule(BaseRole):
    def do_perform(self) -> None:
        self.action.lens_lock()
        self.action.attack()
        if self.action.check_Skill_energy_bar():
            self.action.logger.info("大招就绪")
            for _ in range(10):
                self.action.use_skill()
                time.sleep(0.05)
                self.action.auxiliary_machine()
            self.action.switch()
            print("切换完成")
            return
        elif self.action.check_status("检查核心被动_晖暮"):
            self.action.long_press_dodge(3000)
            s1 = time.time()
            self.combat.context.run_action(
                "长按1号球", pipeline_override={"长按1号球": {"duration": 3500}}
            )
            print("长按完成")
            print("长按耗时:", time.time() - s1)
            self.action.auto_qte("a")
            self.action.auxiliary_machine()
        else:
            self.action.logger.info("核心技能未就绪")
            item = 0
            while self.action.count_signal_balls() < 9 and item < 100:
                if self.action.attack():
                    item += 1
                else:
                    return
        self.action.attack()
        return
