import logging
import time

from custom.action.basics import CombatActions
from custom.action.tool import JobExecutor
from custom.action.tool.Enum import GameActionEnum
from custom.action.tool.LoadSetting import ROLE_ACTIONS

from maa.context import Context
from maa.custom_action import CustomAction


class LostLullaby(CustomAction):
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

            long_press_attack = JobExecutor(
                CombatActions.long_press_attack(context, 1500),
                GameActionEnum.LONG_PRESS_ATTACK,
                role_name=self._role_name,
            )
            ball_elimination = JobExecutor(
                CombatActions.ball_elimination(context),
                GameActionEnum.BALL_ELIMINATION,
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
            if CombatActions.check_status(context, "检查阶段p1_深谣", self._role_name):
                print("p1阶段")
                if CombatActions.check_Skill_energy_bar(context, self._role_name):
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        use_skill.execute()  # 像泡沫一样,消散吧
                    time.sleep(1.5)

                else:
                    if CombatActions.check_status(
                        context, "检查核心被动2_深谣", self._role_name
                    ):
                        print("p1核心被动2")
                        start_time = time.time()
                        while time.time() - start_time < 1:
                            time.sleep(0.1)
                            ball_elimination.execute()  # 从我眼前,消失
                            time.sleep(1)
                            if CombatActions.check_Skill_energy_bar(
                                context, self._role_name
                            ):
                                start_time = time.time()
                                while time.time() - start_time < 1:
                                    time.sleep(0.1)
                                    use_skill.execute()  # 像泡沫一样,消散吧
                                time.sleep(1.5)
                    if CombatActions.check_status(
                        context, "检查核心被动1_深谣", self._role_name
                    ):
                        print("p1核心被动1")
                        time.sleep(0.1)
                        dodge.execute()  # 闪避
                        time.sleep(0.6)
                        ball_elimination_second.execute()  # 消球
                        time.sleep(0.8)
                        start_time = time.time()
                        while time.time() - start_time < 1:
                            time.sleep(0.1)
                            attack.execute()  # 攻击
                    else:
                        print("没有核心被动")
                        start_time = time.time()
                        while time.time() - start_time < 2:
                            time.sleep(0.1)
                            attack.execute()  # 攻击
                        ball_elimination_second.execute()  # 从我眼前,消失

            elif CombatActions.check_status(
                context, "检查阶段p2_深谣", self._role_name
            ):
                print("p2阶段")
                if CombatActions.check_Skill_energy_bar(context, self._role_name):
                    print("释放技能")
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        ball_elimination.execute()  # 滚出这里
                    time.sleep(1)
                    long_press_attack.execute()  # 毁灭吧
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        use_skill.execute()  # 沉没在,这片海底
                    time.sleep(1.5)
                else:
                    if CombatActions.check_status(
                        context, "检查核心被动2_深谣", self._role_name
                    ):
                        print("p2核心被动2")
                        start_time = time.time()
                        while time.time() - start_time < 1:
                            time.sleep(0.1)
                            ball_elimination.execute()  # 滚出这里
                            long_press_attack.execute()  # 毁灭吧
                            time.sleep(0.5)
                        if CombatActions.check_Skill_energy_bar(
                            context, self._role_name
                        ):
                            start_time = time.time()
                            while time.time() - start_time < 1:
                                time.sleep(0.1)
                                use_skill.execute()  # 沉没在,这片海底
                            time.sleep(1.5)
                    elif CombatActions.check_status(
                        context, "检查p2动能条_深谣", self._role_name
                    ):
                        start_time = time.time()
                        while time.time() - start_time < 1:
                            time.sleep(0.1)
                            ball_elimination.execute()  # 滚出这里
                            long_press_attack.execute()  # 毁灭吧
                            time.sleep(0.5)
                        if CombatActions.check_Skill_energy_bar(
                            context, self._role_name
                        ):
                            start_time = time.time()
                            while time.time() - start_time < 1:
                                time.sleep(0.1)
                                use_skill.execute()  # 沉没在,这片海底
                            time.sleep(1.5)
                    else:
                        print("没有核心被动")
                        start_time = time.time()
                        while time.time() - start_time < 1.5:
                            time.sleep(0.3)
                            attack.execute()  # 攻击
                        ball_elimination_second.execute()
            return CustomAction.RunResult(success=True)
        except Exception as e:
            logging.getLogger(f"{self._role_name}_Job").exception(str(e))
            return CustomAction.RunResult(success=False)
