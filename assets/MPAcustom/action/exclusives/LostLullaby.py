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
MAA_Punish 深谣战斗程序
作者:overflow65537,HCX0426
"""


import time
from MPAcustom.action.basics import CombatActions
from maa.context import Context
from maa.custom_action import CustomAction


class LostLullaby(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        actions = CombatActions(context=context, role_name="深谣")

        actions.lens_lock()
        if actions.check_status("检查阶段p1_深谣"):
            actions.logger.info("p1阶段")
            if actions.check_Skill_energy_bar():
                actions.use_skill()  # 像泡沫一样,消散吧

            else:
                if actions.check_status("检查核心被动1_深谣"):
                    actions.logger.info("p1核心被动1")  # 海啸球
                    actions.ball_elimination_target(1)
                    time.sleep(0.3)
                    actions.dodge()  # 闪避

                elif actions.check_status("检查核心被动2_深谣"):
                    actions.logger.info("p1核心被动2")
                    actions.ball_elimination_target(1)

                else:
                    actions.logger.info("没有核心被动")
                    actions.ball_elimination_target(2)
                    actions.continuous_attack(8, 300)

        elif actions.check_status("检查阶段p2_深谣"):
            actions.logger.info("p2阶段")
            if actions.check_Skill_energy_bar():
                for _ in range(10):
                    time.sleep(0.1)
                    actions.ball_elimination_target(1)  # 滚出这里
                time.sleep(1)
                actions.long_press_attack()  # 毁灭吧
                for _ in range(10):
                    time.sleep(0.1)
                    actions.use_skill()  # 沉没在,这片海底

            else:
                actions.ball_elimination_target(1)
                actions.ball_elimination_target(2)
                actions.continuous_attack(8, 300)
        return CustomAction.RunResult(success=True)
