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
MAA_Punish 誓焰战斗程序
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


class Pyroath(CustomAction):
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
            use_skill = JobExecutor(
                CombatActions.use_skill(context),
                GameActionEnum.USE_SKILL,
                role_name=self._role_name,
            )
            long_press_attack = JobExecutor(
                CombatActions.long_press_attack(context),
                GameActionEnum.LONG_PRESS_ATTACK,
                role_name=self._role_name,
            )
            long_press_skill = JobExecutor(
                CombatActions.long_press_skill(context),
                GameActionEnum.LONG_PRESS_SKILL,
                role_name=self._role_name,
            )
            ball_elimination_second = JobExecutor(
                CombatActions.ball_elimination_second(context),
                GameActionEnum.BALL_ELIMINATION_SECOND,
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

            if CombatActions.check_status(context, "检查u1_誓焰", self._role_name):
                print("誓焰u1")
                if CombatActions.check_status(
                    context, "检查p1动能条_誓焰", self._role_name
                ):
                    print("p1动能条max")

                    long_press_skill.execute()  # 汇聚,阳炎之光
                    time.sleep(2)
                    long_press_attack.execute()  # 长按攻击
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        attack.execute()  # 再次点击攻击
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        if CombatActions.check_Skill_energy_bar(
                            context, self._role_name
                        ):
                            use_skill.execute()  # 进入u3阶段
                else:
                    print("p1动能条非max")
                    ball_elimination_second.execute()  # 消球2
                    start_time = time.time()
                    while time.time() - start_time < 2:
                        time.sleep(0.1)
                        attack.execute()

            if CombatActions.check_status(context, "检查u3_誓焰", self._role_name):
                print("誓焰u3")
                if CombatActions.check_status(
                    context, "检查p1动能条_誓焰", self._role_name
                ):
                    print("p3动能条max")
                    long_press_attack = JobExecutor(
                        CombatActions.long_press_attack(context, 4000),
                        GameActionEnum.LONG_PRESS_ATTACK,
                        role_name=self._role_name,
                    ).execute()
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        if CombatActions.check_Skill_energy_bar(
                            context, self._role_name
                        ):
                            use_skill.execute()  # 越过迷雾,与深渊
                            time.sleep(0.1)
                            trigger_qte_first.execute()
                            trigger_qte_second.execute()
                            auxiliary_machine.execute()
                else:
                    print("p3动能条非max")
                    start_time = time.time()
                    while time.time() - start_time < 2:
                        time.sleep(0.1)
                        attack.execute()  # 攻击

            if CombatActions.check_status(context, "检查u2_誓焰", self._role_name):
                print("誓焰u2")
                ball_elimination_second.execute()  # 消球2
                attack.execute()  # 攻击
                use_skill.execute()  # 进入u3阶段
                time.sleep(0.2)
                if CombatActions.check_status(
                    context, "检查p1动能条_誓焰", self._role_name
                ):
                    if CombatActions.check_status(
                        context, "检查u2_誓焰", self._role_name
                    ):
                        long_press_attack.execute()  # 长按攻击
                        start_time = time.time()
                        while time.time() - start_time < 1:
                            time.sleep(0.1)
                            attack.execute()  # 再次点击攻击
                        start_time = time.time()
                        while time.time() - start_time < 1:
                            time.sleep(0.1)
                            ball_elimination_second.execute()  # 消球2
                            time.sleep(0.1)
                            attack.execute()  # 攻击
                            time.sleep(0.1)
                            use_skill.execute()  # 进入u3阶段
                else:
                    if CombatActions.check_status(
                        context, "检查u2max_誓焰", self._role_name
                    ):
                        start_time = time.time()
                        while time.time() - start_time < 1:
                            time.sleep(0.1)
                            ball_elimination_second.execute()  # 消球2
                            time.sleep(0.1)
                            attack.execute()  # 攻击
                            time.sleep(0.1)
                            if CombatActions.check_Skill_energy_bar(
                                context, self._role_name
                            ):
                                use_skill.execute()  # 进入u3阶段

                            return CustomAction.RunResult(success=True)
                    ball_elimination_second.execute()  # 消球2
                    start_time = time.time()
                    while time.time() - start_time < 2:
                        time.sleep(0.1)
                        ball_elimination_second.execute()  # 消球2
                        time.sleep(0.1)
                        attack.execute()  # 攻击

            return CustomAction.RunResult(success=True)
        except Exception as e:
            logging.getLogger(f"{self._role_name}_Job").exception(str(e))
            return CustomAction.RunResult(success=False)
