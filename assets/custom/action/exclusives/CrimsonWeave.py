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

import logging
import time

from custom.action.basics import CombatActions
from custom.action.tool import JobExecutor
from custom.action.tool.Enum import GameActionEnum
from custom.action.tool.LoadSetting import ROLE_ACTIONS

from maa.context import Context
from maa.custom_action import CustomAction


class CrimsonWeave(CustomAction):
    def __init__(self):
        super().__init__()
        for name, action in ROLE_ACTIONS.items():
            if action in self.__class__.__name__:
                self._role_name = name

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
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
            dodge = JobExecutor(
                CombatActions.dodge(context),
                GameActionEnum.DODGE,
                role_name=self._role_name,
            )

            use_skill = JobExecutor(
                CombatActions.use_skill(context),
                GameActionEnum.USE_SKILL,
                role_name=self._role_name,
            )
            long_press_dodge = JobExecutor(
                CombatActions.long_press_dodge(context, 1500),
                GameActionEnum.LONG_PRESS_DODGE,
                role_name=self._role_name,
            )
            long_press_attack = JobExecutor(
                CombatActions.long_press_attack(context, 2500),
                GameActionEnum.LONG_PRESS_ATTACK,
                role_name=self._role_name,
            )
            ball_elimination = JobExecutor(
                CombatActions.ball_elimination(context),
                GameActionEnum.BALL_ELIMINATION,
                role_name=self._role_name,
            )
            trigger_qte_first = JobExecutor(
                CombatActions.trigger_qte_first(context),
                GameActionEnum.TRIGGER_QTE_FIRST,
                role_name=self._role_name,
            )
            trigger_qte_second = JobExecutor(
                CombatActions.trigger_qte_second(context),
                GameActionEnum.TRIGGER_QTE_SECOND,
                role_name=self._role_name,
            )
            auxiliary_machine = JobExecutor(
                CombatActions.auxiliary_machine(context),
                GameActionEnum.AUXILIARY_MACHINE,
                role_name=self._role_name,
            )
            lens_lock.execute()

            if CombatActions.check_Skill_energy_bar(context, self._role_name):
                if CombatActions.check_status(
                    context, "检查u1_囚影", self._role_name
                ):  # 一阶段
                    use_skill.execute()  # 崩落的束缚化为利刃
                    time.sleep(0.3)
                    long_press_attack.execute()  # 登龙

                if CombatActions.check_status(
                    context, "检查u2_囚影", self._role_name
                ):  # 二阶段
                    if CombatActions.check_status(
                        context, "检查无光值_囚影", self._role_name
                    ):  # 检查无光值大于474
                        long_press_attack.execute()  # 登龙
                        ball_elimination.execute()  # 消球
                        time.sleep(0.4)
                        ball_elimination.execute()  # 消球

                    else:
                        use_skill.execute()  # 宿命的囚笼由我斩断
                        for _ in range(2):
                            time.sleep(0.2)
                            trigger_qte_first.execute()
                            trigger_qte_second.execute()
                            auxiliary_machine.execute()
            else:
                ball_elimination.execute()  # 消球
                time.sleep(1)
                ball_elimination.execute()  # 消球
                dodge.execute()  # 闪避
                start_time = time.time()
                while time.time() - start_time < 1.5:
                    time.sleep(0.1)
                    attack.execute()  # 攻击
                ball_elimination.execute()  # 消球
                long_press_dodge.execute()  # 长按闪避
                if CombatActions.check_status(context, "检查u2_囚影", self._role_name):
                    long_press_attack.execute()  # 登龙

            return CustomAction.RunResult(success=True)
        except Exception as e:
            logging.getLogger(f"{self._role_name}_Job").exception(str(e))
            return CustomAction.RunResult(success=False)
