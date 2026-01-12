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


from MPAcustom.action.basics import CombatActions
from maa.context import Context
from maa.custom_action import CustomAction
import time


class Limpidity(CustomAction):
    """
    丽芙霁梦 战斗逻辑
    优先级:
    1. 必杀技
    2. 普攻形态1 + 核心
    3. 普攻形态2
    4. 默认普攻
    """

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        action = CombatActions(context, role_name="丽芙·霁梦")
        action.lens_lock()
        action.attack()

        # 检查普攻1
        if action.check_status("检查普攻1_霁梦"):
            if action.check_status("检查核心条_霁梦"):
                action.long_press_dodge(1000)  # 直面天闪!
                action.auto_qte("a")
                print("直面天闪!")
                for _ in range(15):
                    action.use_skill()  # 以苦厄,澈我心镜
                    action.auxiliary_machine()
                    action.attack()
                    time.sleep(0.1)
                print("以苦厄,澈我心镜")
                action.attack()
                return CustomAction.RunResult(success=True)

            # 信号球消除逻辑
            target = action.Arrange_Signal_Balls()
            if target > 0 or action.count_signal_balls() >= 5:
                action.ball_elimination_target(target)
                time.sleep(0.2)
                action.attack()
                return CustomAction.RunResult(success=True)

        # 检查普攻2
        if action.check_status("检查普攻2_霁梦"):
            if action.check_status("检查核心球_霁梦"):
                start_time = time.time()
                while not action.check_status("检查核心条2_霁梦"):
                    if context.tasker.stopping:
                        return CustomAction.RunResult(success=True)
                    if time.time() - start_time > 5:
                        return CustomAction.RunResult(success=True)
                    action.ball_elimination_target(1)  # 见证,我的意志
                    print("见证,我的意志")
                    time.sleep(0.1)
                action.auto_qte("a")

                action.long_press_attack(3000)  # 终于,梦醒时分
                print("终于,梦醒时分")
                for _ in range(15):
                    action.use_skill()  # 映天地,渡你新生
                    action.auxiliary_machine()
                    time.sleep(0.1)
                print("映天地,渡你新生")
                action.attack()

                return CustomAction.RunResult(success=True)

            elif action.count_signal_balls() != 0:
                action.ball_elimination_target()
                action.attack()
                return CustomAction.RunResult(success=True)

        for _ in range(30):
            action.attack()
            time.sleep(0.1)

        return CustomAction.RunResult(success=True)
