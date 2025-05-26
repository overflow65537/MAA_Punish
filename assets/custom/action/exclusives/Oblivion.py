import logging
import time

from custom.action.basics import CombatActions
from custom.action.tool import JobExecutor
from custom.action.tool.Enum import GameActionEnum
from custom.action.tool.LoadSetting import ROLE_ACTIONS

from maa.context import Context
from maa.custom_action import CustomAction


class Oblivion(CustomAction):
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

            use_skill = JobExecutor(
                CombatActions.use_skill(context),
                GameActionEnum.USE_SKILL,
                role_name=self._role_name,
            )
            long_press_attack = JobExecutor(
                CombatActions.long_press_attack(context, 2100),
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
            # 等待时间为技能动画时间
            lens_lock.execute()
            if CombatActions.check_status(context, "检查残月值_终焉", self._role_name):
                long_press_attack.execute()
                if CombatActions.check_Skill_energy_bar(context, self._role_name):
                    use_skill.execute()
                    for _ in range(2):  # 防止未触发QTE和辅助机
                        time.sleep(0.3)
                        trigger_qte_first.execute()
                        trigger_qte_second.execute()
                        auxiliary_machine.execute()
                else:
                    ball_elimination.execute()
                    time.sleep(0.1)
                    ball_elimination.execute()
                    long_press_attack.execute()
                    if CombatActions.check_Skill_energy_bar(context, self._role_name):
                        use_skill.execute()
                        for _ in range(2):
                            time.sleep(0.3)
                            trigger_qte_first.execute()
                            trigger_qte_second.execute()
                            auxiliary_machine.execute()
            else:
                ball_elimination.execute()
                time.sleep(0.1)
                ball_elimination.execute()
                if not CombatActions.check_status(
                    context, "检查残月值_终焉", self._role_name
                ):
                    long_press_attack.execute()
                    if CombatActions.check_Skill_energy_bar(context, self._role_name):
                        use_skill.execute()
                        for _ in range(2):
                            time.sleep(0.3)
                            trigger_qte_first.execute()
                            trigger_qte_second.execute()
                            auxiliary_machine.execute()

            return CustomAction.RunResult(success=True)
        except Exception as e:
            logging.getLogger(f"{self._role_name}_Job").exception(str(e))
            return CustomAction.RunResult(success=False)
