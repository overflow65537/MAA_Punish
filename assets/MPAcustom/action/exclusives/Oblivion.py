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
MAA_Punish 终焉战斗程序
作者:overflow65537,HCX0426
"""


import time

from MPAcustom.action.basics import CombatActions
from maa.context import Context
from maa.custom_action import CustomAction


class Oblivion(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        actions = CombatActions(context, role_name="终焉")

        actions.lens_lock()

        if actions.check_Skill_energy_bar():
            actions.use_skill(1000)  # 技能
        elif actions.check_status("检查残月值_终焉"):
            actions.long_press_attack(2000)
        elif actions.count_signal_balls() >= 9:
            actions.ball_elimination_target(1)
        else:
            time.sleep(0.1)
            actions.ball_elimination_target(1)
            actions.continuous_attack(8, 200)
            actions.long_press_attack(2000)
            time.sleep(1)

        return CustomAction.RunResult(success=True)
