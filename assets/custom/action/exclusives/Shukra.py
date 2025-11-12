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
MAA_Punish 启明战斗程序
作者:overflow65537
"""


import time


from custom.action.basics import CombatActions


from maa.context import Context
from maa.custom_action import CustomAction


class Shukra(CustomAction):
    """
    启明战斗逻辑
    检查是否存在大招
        释放大招
    检查信号球数量信号球数量大于9
        7秒内循环
            识别信号球
            消球
            如果刚才的球是三消
                再消球触发核心技能
            如果没有球了
                结束
        结束后长按攻击尝试触发冰山
    检查信号球数量信号球数量小于9
        攻击攒球
    """

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:

        actions = CombatActions(context,role_name="启明")

        actions.lens_lock()

        if actions.check_Skill_energy_bar():
            actions.use_skill()  # 万世生死,淬于寒冰
            start_time = time.time()
            while time.time() - start_time < 3:  # 生死喧嚣,归于寂静
                time.sleep(0.1)
                actions.ball_elimination_target(1)

        elif actions.count_signal_balls() >= 9:  # 信号球数量大于9
            start_time = time.time()
            while time.time() - start_time < 7:
                time.sleep(0.3)
                target = actions.Arrange_Signal_Balls("any")
                actions.ball_elimination_target(target)
                actions.logger.info(f"初次消球")
                if target > 0:
                    time.sleep(0.1)
                    actions.logger.info(f"三连目标,开始二次消球")
                    actions.ball_elimination_target(1)  # 单独消球
                elif target == 0:
                    actions.logger.info(f"信号球空,结束")
                    break
            actions.logger.info(f"长按攻击")
            actions.long_press_attack()
        else:
            actions.logger.info(f"普攻")
            start_time = time.time()
            while time.time() - start_time < 2:
                actions.attack()  # 攻击
                time.sleep(0.1)
        return CustomAction.RunResult(success=True)
