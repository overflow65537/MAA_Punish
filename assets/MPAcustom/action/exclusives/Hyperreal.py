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
MAA_Punish 超刻战斗程序
作者:overflow65537
"""

import time


from maa.context import Context
from maa.custom_action import CustomAction
from MPAcustom.action.basics import CombatActions


class Hyperreal(CustomAction):

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:

        action = CombatActions(context=context, role_name="超刻")

        action.lens_lock()

        if action.check_Skill_energy_bar():
            action.logger.info("大招就绪")
            action.use_skill()  # 在时间的尽头,湮灭吧
            action.auxiliary_machine()
            time.sleep(1)
            action.auto_qte("a")

        elif action.check_status("检查核心技能_超刻"):  # 核心技能就绪
            action.logger.info("核心技能就绪")
            action.long_press_attack()
            action.auto_qte("a")
            action.auxiliary_machine()

            start_time = time.time()
            while (
                not action.check_status("检查核心技能结束_超刻")
            ) and time.time() - start_time < 10:
                while action.count_signal_balls() and time.time() - start_time < 10:
                    action.ball_elimination_target(1)

                time.sleep(0.1)
                action.auto_qte("a")
                action.attack()
            action.logger.info("核心技能结束")

        else:
            action.logger.info("核心技能未就绪")
            action.continuous_attack(5, 100)
            target = action.Arrange_Signal_Balls("any")
            if action.count_signal_balls() >= 9 or target > 0:
                action.ball_elimination_target(target)
        return CustomAction.RunResult(success=True)
