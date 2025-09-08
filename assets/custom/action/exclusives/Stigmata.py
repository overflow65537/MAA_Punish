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
MAA_Punish 深痕战斗程序
作者:overflow65537,HCX0426
"""


import time

from custom.action.basics import CombatActions


from maa.context import Context
from maa.custom_action import CustomAction


class Stigmata(CustomAction):

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        actions = CombatActions(context, role_name="深痕")

        actions.lens_lock()
        if actions.check_Skill_energy_bar():
            actions.use_skill()  # 此刻,见证终焉之光/以此宣告,噩梦的崩解
            return CustomAction.RunResult(success=True)

        elif actions.check_status("检查比安卡·深痕一阶段"):
            if actions.check_status("检查核心被动_深痕"):
                actions.long_press_dodge()  # 开启照域
                for _ in range(10):
                    actions.ball_elimination_target(1)  # 消球
                    time.sleep(0.3)
                    actions.attack()
                    time.sleep(0.1)
                return CustomAction.RunResult(success=True)

        actions.continuous_attack(8, 300)

        return CustomAction.RunResult(success=True)
