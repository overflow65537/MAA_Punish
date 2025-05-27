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
MAA_Punish 深痕战斗程序
作者:overflow65537,HCX0426
"""


import logging
import sys
import time
from pathlib import Path

from custom.action.basics import CombatActions
from custom.action.tool import JobExecutor
from custom.action.tool.Enum import GameActionEnum
from custom.action.tool.LoadSetting import ROLE_ACTIONS

from maa.context import Context
from maa.custom_action import CustomAction


class Stigmata(CustomAction):
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
                CombatActions.long_press_attack(context, 3000),
                GameActionEnum.LONG_PRESS_ATTACK,
                role_name=self._role_name,
            )
            long_press_dodge = JobExecutor(
                CombatActions.long_press_dodge(context),
                GameActionEnum.LONG_PRESS_DODGE,
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
            if CombatActions.check_status(
                context, "检查比安卡·深痕一阶段", self._role_name
            ):
                if not CombatActions.check_status(
                    context, "检查u1_深痕", self._role_name
                ):
                    if CombatActions.check_status(
                        context, "检查核心被动_深痕", self._role_name
                    ):
                        long_press_dodge.execute()  # 开启照域
                        start_time = time.time()
                        while time.time() - start_time < 4:
                            ball_elimination.execute()  # 消球
                            time.sleep(0.5)
                            attack.execute()
                            time.sleep(0.1)
            if CombatActions.check_Skill_energy_bar(context, self._role_name):
                if CombatActions.check_status(context, "检查u1_深痕", self._role_name):
                    use_skill.execute()  # 此刻,见证终焉之光
                    time.sleep(1)
                if CombatActions.check_status(context, "检查u2_深痕", self._role_name):
                    use_skill.execute()  # 以此宣告,噩梦的崩解
                    for _ in range(2):
                        time.sleep(1.5)
                        trigger_qte_first.execute()
                        trigger_qte_second.execute()
                        auxiliary_machine.execute()
                    time.sleep(1.8)
                else:
                    if not CombatActions.check_status(
                        context, "检查u2数值_深痕", self._role_name
                    ):  # 残光值大于90
                        start_time = time.time()
                        while time.time() - start_time < 2:
                            attack.execute()  # 攻击
                            time.sleep(0.1)
                        long_press_attack.execute()  # 长按攻击
            else:
                start_time = time.time()
                while time.time() - start_time < 2:
                    attack.execute()  # 攻击
                    time.sleep(0.1)
                long_press_attack.execute()  # 长按攻击

            return CustomAction.RunResult(success=True)
        except Exception as e:
            logging.getLogger(f"{self._role_name}_Job").exception(str(e))
            return CustomAction.RunResult(success=False)
