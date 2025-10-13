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
from custom.action.basics import CombatActions
from maa.context import Context
from maa.custom_action import CustomAction


class Pyroath(CustomAction):

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:

        actions = CombatActions(context, role_name="誓焰")

        actions.lens_lock()

        if actions.check_status("检查u1_誓焰"):
            actions.logger.info("誓焰u1")
            if actions.check_status("检查p1动能条_誓焰"):
                actions.logger.info("p1动能条max")
                actions.long_press_skill()  # 汇聚,阳炎之光
            else:
                actions.logger.info("p1动能条非max")
                actions.ball_elimination_target()  # 消球2
                actions.continuous_attack(20, 100)  # 攻击

        elif actions.check_status("检查u2_誓焰"):
            actions.logger.info("誓焰u2")
            if actions.check_Skill_energy_bar():
                actions.use_skill()  # 进入3阶段
            else:
                actions.long_press_attack()
                actions.continuous_attack(20, 100)  # 攻击
                actions.ball_elimination_target()  # 消球2

        elif actions.check_status("检查u3_誓焰"):
            actions.logger.info("誓焰u3")
            if actions.check_Skill_energy_bar():
                actions.use_skill()
            else:
                actions.long_press_attack(4000)  # 长按攻击
                actions.use_skill()
                time.sleep(0.1)
                actions.auxiliary_machine()

        return CustomAction.RunResult(success=True)
