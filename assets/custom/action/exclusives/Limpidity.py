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


from custom.action.basics import CombatActions
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

        # 检查普攻1
        if action.check_status("检查普攻1_霁梦"):
            action.logger.info("检测到普攻形态1")
            if action.check_status("检查核心条_霁梦"):
                action.logger.info("核心已就绪，长按闪避")
                action.long_press_dodge(1000)
                for _ in range(15):
                    action.use_skill()
                    action.attack()
                    time.sleep(0.1)
                return CustomAction.RunResult(success=True)

            # 信号球消除逻辑
            target = action.Arrange_Signal_Balls()
            if target > 0 or action.count_signal_balls() >= 5:
                action.ball_elimination_target(target)
                time.sleep(0.2)
                return CustomAction.RunResult(success=True)

        # 检查普攻2
        if action.check_status("检查普攻2_霁梦"):
            action.logger.info("检测到普攻形态2")
            if action.check_status("检查核心球_霁梦"):
                action.logger.info("核心球已就绪，进行核心球消除")
                start_time = time.time()
                while not action.check_status("检查核心条2_霁梦"):
                    if context.tasker.stopping:
                        return CustomAction.RunResult(success=True)
                    if time.time() - start_time > 5:
                        action.logger.info("等待核心条就绪超时，跳出循环")
                        return CustomAction.RunResult(success=True)
                    action.ball_elimination_target(1)
                    time.sleep(0.1)

                action.long_press_attack(3000)
                for _ in range(15):
                    action.use_skill()
                    time.sleep(0.1)

                return CustomAction.RunResult(success=True)

            elif action.count_signal_balls() != 0:
                action.ball_elimination_target()
                return CustomAction.RunResult(success=True)

        # 默认普攻
        action.logger.info("默认状态，执行连续普攻")
        for _ in range(30):
            action.attack()
            time.sleep(0.1)

        return CustomAction.RunResult(success=True)
