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

        action = CombatActions(context, role_name="誓焰")

        action.lens_lock()

        if action.check_status("检查u1_誓焰"):
            action.logger.info("誓焰u1")
            if action.check_status("检查p1动能条_誓焰"):
                action.logger.info("p1动能条max")
                action.long_press_skill()  # 汇聚,阳炎之光
            else:
                action.logger.info("p1动能条非max")
                action.ball_elimination_target()  # 消球2
                action.continuous_attack(20, 100)  # 攻击

        elif action.check_status("检查u2_誓焰"):
            action.logger.info("誓焰u2")
            if action.check_Skill_energy_bar():
                action.use_skill()  # 进入3阶段
            else:
                action.long_press_attack()
                action.continuous_attack(20, 100)  # 攻击
                action.ball_elimination_target()  # 消球2

        elif action.check_status("检查u3_誓焰"):
            action.logger.info("誓焰u3")
            if action.check_Skill_energy_bar():
                action.use_skill()
            elif not action.check_status("检查u3_max"):
                action.attack()
                for _ in range(10):
                    time.sleep(0.3)
                    action.attack()
            action.long_press_attack(4000)  # 长按攻击
            action.use_skill()
            time.sleep(0.5)
            action.auxiliary_machine()
            action.trigger_qte(1)
            action.trigger_qte(2)

        return CustomAction.RunResult(success=True)
