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
MAA_Punish 囚影战斗程序
作者:overflow65537,HCX0426
"""

import time
from custom.action.basics import CombatActions
from maa.context import Context
from maa.custom_action import CustomAction


class CrimsonWeave(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:

        action = CombatActions(context, role_name="露西亚·深红囚影")
        action.lens_lock()

        if (
            action.check_status("检查u1_囚影") and action.check_Skill_energy_bar()
        ):  # 一阶段
            action.use_skill(1500)  # 崩落的束缚化为利刃

        elif action.check_status("检查u2_囚影"):  # 二阶段
            if action.check_status("检查无光值_囚影"):  # 检查无光值大于474
                action.long_press_dodge(1500)  # 闪避
                action.long_press_attack(2300)  # 登龙
                for _ in range(10):
                    action.use_skill()  # 二段大
                    action.auxiliary_machine()
                    time.sleep(0.2)
                return CustomAction.RunResult(success=True)
        time.sleep(0.2)
        action.ball_elimination_target(1)
        time.sleep(0.2)
        action.dodge()  # 闪避
        action.continuous_attack(7, 300)
        return CustomAction.RunResult(success=True)
