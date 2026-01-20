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
        action = CombatActions(context, role_name="终焉")

        action.lens_lock()
        action.attack()

        if action.check_Skill_energy_bar():
            action.use_skill(1000)  # 技能
            action.auxiliary_machine()
            action.auto_qte("a")
            time.sleep(0.1)
            loop_count = 0
            while not action.check_Skill_energy_bar() and loop_count < 30:
                if context.tasker.stopping:
                    return CustomAction.RunResult(success=True)
                inside_item = 0
                action.attack()
                while (
                    action.count_signal_balls()
                    and inside_item < 5
                    and not action.check_Skill_energy_bar()
                ):
                    action.ball_elimination_target(1)
                    inside_item += 1
                    action.attack()
                    action.auto_qte("a")
                action.attack()
                if (
                    action.check_status("检查残月值_终焉")
                    and not action.check_Skill_energy_bar()
                ):
                    action.long_press_attack(2000)
                loop_count += 1
            action.use_skill(1000)  # 技能
            action.auxiliary_machine()
            action.auto_qte("a")
            for _ in range(10):
                action.attack()
            action.switch()
            print("切换完成")
            return CustomAction.RunResult(success=True)

        else:
            for _ in range(30):
                if context.tasker.stopping or action.check_Skill_energy_bar():
                    return CustomAction.RunResult(success=True)
                item = 0
                action.attack()
                while action.count_signal_balls() and item < 5:
                    action.ball_elimination_target(1)
                    item += 1
                    action.attack()
                    action.auto_qte("a")
                action.attack()
                if action.check_status("检查残月值_终焉"):
                    action.long_press_attack(2000)
        action.attack()

        return CustomAction.RunResult(success=True)
