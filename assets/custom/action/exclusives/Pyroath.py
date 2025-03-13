import logging
import sys
import time
from pathlib import Path

# 获取当前文件的绝对路径
current_file = Path(__file__).resolve()

# 定义可能的项目根目录相对路径
root_paths = [
    current_file.parent.parent.parent.parent.joinpath("MFW_resource"),
    current_file.parent.parent.parent.parent.parent.parent.joinpath("Bundles").joinpath("MAA_Punish"),
    current_file.parent.parent.parent.parent.parent.joinpath("assets"),
]

# 确定项目根目录
project_root = next((path for path in root_paths if path.exists()), None)
if project_root:
    if project_root == current_file.parent.parent.parent.parent.joinpath("MFW_resource"):
        project_root = current_file.parent.parent.parent.parent
    print(f"项目根目录: {project_root}")
    # 添加项目根目录到sys.path
    sys.path.append(str(project_root))
    from custom.action.basics import CombatActions
    from custom.action.tool import JobExecutor
    from custom.action.tool.Enum import GameActionEnum
    from custom.action.tool.LoadSetting import ROLE_ACTIONS
else:
    from assets.custom.action.basics import CombatActions
    from assets.custom.action.tool import JobExecutor
    from assets.custom.action.tool.Enum import GameActionEnum
    from assets.custom.action.tool.LoadSetting import ROLE_ACTIONS

from maa.context import Context
from maa.custom_action import CustomAction


class Pyroath(CustomAction):
    def __init__(self):
        super().__init__()
        for name, action in ROLE_ACTIONS.items():
            if action == self.__class__.__name__:
                self._role_name = name

    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        try:
            lens_lock = JobExecutor(
                CombatActions.lens_lock(context), GameActionEnum.LENS_LOCK, role_name=self._role_name
            )
            attack = JobExecutor(CombatActions.attack(context), GameActionEnum.ATTACK, role_name=self._role_name)
            use_skill = JobExecutor(
                CombatActions.use_skill(context), GameActionEnum.USE_SKILL, role_name=self._role_name
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
                CombatActions.trigger_qte_first(context), GameActionEnum.TRIGGER_QTE_FIRST, role_name=self._role_name
            )
            trigger_qte_second = JobExecutor(
                CombatActions.trigger_qte_second(context), GameActionEnum.TRIGGER_QTE_SECOND, role_name=self._role_name
            )
            auxiliary_machine = JobExecutor(
                CombatActions.auxiliary_machine(context), GameActionEnum.AUXILIARY_MACHINE, role_name=self._role_name
            )
            lens_lock.execute()

            if CombatActions.check_status(context, "检查u1_誓焰", self._role_name):
                print("誓焰u1")
                if CombatActions.check_status(context, "检查p1动能条_誓焰", self._role_name):
                    print("p1动能条max")
                    long_press_skill.execute()  # 汇聚,阳炎之光

                    long_press_attack.execute()  # 长按攻击
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        attack.execute()  # 再次点击攻击
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        use_skill.execute()  # 进入u3阶段

                else:
                    print("p1动能条非max")
                    ball_elimination_second.execute()  # 消球2
                    start_time = time.time()
                    while time.time() - start_time < 2:
                        time.sleep(0.1)
                        attack.execute()

            elif CombatActions.check_status(context, "检查u2_誓焰", self._role_name):
                print("誓焰u2")
                ball_elimination_second.execute()  # 消球2
                attack.execute()  # 攻击
                use_skill.execute()  # 进入u3阶段
                if CombatActions.check_status(context, "检查p1动能条_誓焰", self._role_name):
                    print("p2动能条max")
                    if CombatActions.check_status(context, "检查u2_誓焰", self._role_name):
                        long_press_attack.execute()  # 长按攻击
                        start_time = time.time()
                        while time.time() - start_time < 1:
                            time.sleep(0.1)
                            attack.execute()  # 再次点击攻击
                        start_time = time.time()
                        while time.time() - start_time < 1:
                            time.sleep(0.1)
                            ball_elimination_second.execute()  # 消球2
                            attack.execute()  # 攻击
                            use_skill.execute()  # 进入u3阶段

                else:
                    if CombatActions.check_status(context, "检查u2max_誓焰", self._role_name):
                        print("p2动能条max")
                        start_time = time.time()
                        while time.time() - start_time < 1:
                            time.sleep(0.1)
                            ball_elimination_second.execute()  # 消球2
                            attack.execute()  # 攻击
                            use_skill.execute()  # 进入u3阶段

                            return CustomAction.RunResult(success=True)
                    print("p2动能条非max")
                    ball_elimination_second.execute()  # 消球2
                    start_time = time.time()
                    while time.time() - start_time < 2:
                        time.sleep(0.1)
                        ball_elimination_second.execute()  # 消球2
                        attack.execute()  # 攻击

            elif CombatActions.check_status(context, "检查u3_誓焰", self._role_name):
                print("誓焰u3")
                if CombatActions.check_status(context, "检查p1动能条_誓焰", self._role_name):
                    print("p3动能条max")
                    long_press_attack = JobExecutor(
                        CombatActions.long_press_attack(context, 4000),
                        GameActionEnum.LONG_PRESS_ATTACK,
                        role_name=self._role_name,
                    ).execute()
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        use_skill.execute()  # 越过迷雾,与深渊
                        trigger_qte_first.execute()
                        trigger_qte_second.execute()
                        auxiliary_machine.execute()
                else:
                    print("p3动能条非max")
                    start_time = time.time()
                    while time.time() - start_time < 2:
                        time.sleep(0.1)
                        attack.execute()  # 攻击
            else:
                use_skill.execute()

            return CustomAction.RunResult(success=True)
        except Exception as e:
            logging.getLogger(f"{self._role_name}_Job").exception(str(e))
            return CustomAction.RunResult(success=False)
