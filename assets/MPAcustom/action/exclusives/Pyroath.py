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
MAA_Punish 誓焰战斗程序
作者:overflow65537,HCX0426
"""


import time
from MPAcustom.action.basics import CombatActions
from maa.context import Context
from maa.custom_action import CustomAction


class Pyroath(CustomAction):

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:

        self.action = CombatActions(context, role_name="誓焰")

        start_time = time.time()
        print(f"启动时间: {start_time}")
        self.action.lens_lock()
        self.action.attack()

        if self.action.check_status("检查u1_誓焰"):
            self.action.logger.info("誓焰u1")
            print("u1, 攻击")
            atk_items = 0
            while not self.action.check_status("检查p1动能条_誓焰") and atk_items < 100:
                self.action.ball_elimination_target()  # 消球2
                self.action.attack()
                time.sleep(0.05)
                atk_items += 1

            self.action.logger.info("p1动能条max")
            print("p1动能条max, 汇聚,阳炎之光")
            self.action.long_press_skill()  # 汇聚,阳炎之光
            time.sleep(0.1)
            self.action.auto_qte("a")
            print("长按攻击")
            start_time = time.time()
            while time.time() - start_time < 1.5:
                if self.action.check_status("检查p1动能条_誓焰"):
                    self.action.long_press_attack(700)
                self.action.attack()

        elif self.action.check_status("检查u2_誓焰"):
            self.action.logger.info("誓焰u2")
            print("u2, 攻击")

            atk_items = 0
            while not self.action.check_Skill_energy_bar() and atk_items < 20:
                self.action.attack()
                time.sleep(0.05)
                self.action.ball_elimination_target()
                time.sleep(0.05)
                atk_items += 1
            self.action.use_skill()
        elif self.action.check_status("检查u3_誓焰"):
            print("u3, 攻击")
            self.action.logger.info("誓焰u3")
            atk_items = 0
            while not self.action.check_status("检查u3_max") and atk_items < 20:
                self.action.attack()
                time.sleep(0.3)
                atk_items += 1
            self.action.long_press_attack(4000)  # 长按攻击
            self.action.use_skill()
            time.sleep(0.1)
            self.action.auxiliary_machine()
            self.action.auto_qte("a")
        self.action.attack()
        end_time = time.time()
        print(f"誓焰: {end_time - start_time}")
        print(f"结束时间: {end_time}")

        return CustomAction.RunResult(success=True)
