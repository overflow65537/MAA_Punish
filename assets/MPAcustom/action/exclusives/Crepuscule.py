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
MAA_Punish 晖暮战斗程序
作者:overflow65537
"""

import time
from MPAcustom.action.basics import CombatActions
from maa.context import Context
from maa.custom_action import CustomAction


class Crepuscule(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        action = CombatActions(context, role_name="晖暮")

        action.lens_lock()
        action.attack()
        if action.check_Skill_energy_bar():
            action.logger.info("大招就绪")
            for _ in range(10):
                action.use_skill()
                time.sleep(0.05)
                action.auxiliary_machine()
            action.switch()
            print("切换完成")
            return CustomAction.RunResult(success=True)

        elif action.check_status("检查核心被动_晖暮"):
            action.long_press_dodge(3000)
            context.run_action("长按1号球")
            action.auto_qte("a")
            action.auxiliary_machine()
        else:
            action.logger.info("核心技能未就绪")
            item = 0
            while action.count_signal_balls() < 9 and item < 100:
                action.attack()
                item += 1
        action.attack()
        return CustomAction.RunResult(success=True)
