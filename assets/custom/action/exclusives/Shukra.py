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

import logging
import time

from custom.action.basics import CombatActions
from custom.action.tool import JobExecutor
from custom.action.tool.Enum import GameActionEnum
from custom.action.tool.LoadSetting import ROLE_ACTIONS

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

    tempelate = {
        "red": {"识别信号球": {"template": ["信号球/启明_红.png"]}},
        "blue": {"识别信号球": {"template": ["信号球/启明_蓝.png"]}},
        "yellow": {"识别信号球": {"template": ["信号球/启明_黄.png"]}},
    }

    def __init__(self):
        super().__init__()
        for name, action in ROLE_ACTIONS.items():
            if action in self.__class__.__name__:
                self._role_name = name

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:

        def get_ball_target():
            return CombatActions.Arrange_Signal_Balls(
                context,
                "any",
                self.tempelate,
                role_name=self._role_name,
            )
        logger = logging.getLogger(f"{self._role_name}_Job")

        try:
            lens_lock = JobExecutor(
                CombatActions.lens_lock(context),
                GameActionEnum.LENS_LOCK,
                role_name=self._role_name,
            )
            attack = JobExecutor(
                CombatActions.attack(context),
                GameActionEnum.ATTACK,
                role_name=self._role_name,
            )

            use_skill = JobExecutor(
                CombatActions.use_skill(context),
                GameActionEnum.USE_SKILL,
                role_name=self._role_name,
            )
            long_press_attack = JobExecutor(
                CombatActions.long_press_attack(context, 3000),
                GameActionEnum.LONG_PRESS_ATTACK,
                role_name=self._role_name,
            )
            lens_lock.execute()

            if CombatActions.check_Skill_energy_bar(context, self._role_name):
                use_skill.execute()  # 万世生死,淬于寒冰
                start_time = time.time()
                while time.time() - start_time < 3:  # 生死喧嚣,归于寂静
                    time.sleep(0.1)
                    CombatActions.ball_elimination_target(context, 1)()

            elif CombatActions.check_status(
                context, "检查信号球数量_启明", self._role_name
            ):  # 信号球数量大于9
                start_time = time.time()
                while time.time() - start_time < 7:
                    time.sleep(0.3)
                    target = get_ball_target()
                    CombatActions.ball_elimination_target(context, target)()
                    logger.info(f"初次消球")
                    if target > 0:
                        time.sleep(0.1)
                        logger.info(f"三连目标,开始二次消球")
                        CombatActions.ball_elimination_target(context, 1)()  # 单独消球
                    elif target == 0:
                        logger.info(f"信号球空,结束")
                        break
                logger.info(f"长按攻击")
                long_press_attack.execute()
            else:
                logger.info(f"普攻")
                start_time = time.time()
                while time.time() - start_time < 2:
                    attack.execute()  # 攻击
                    time.sleep(0.1)
            return CustomAction.RunResult(success=True)
        except Exception as e:
            logging.getLogger(f"{self._role_name}_Job").exception(str(e))
            return CustomAction.RunResult(success=False)
