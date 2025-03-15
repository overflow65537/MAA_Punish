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


class LostLullaby(CustomAction):
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
            attack = JobExecutor(
                CombatActions.attack(context), GameActionEnum.ATTACK, role_name=self._role_name
            )
            dodge = JobExecutor(
                CombatActions.dodge(context), GameActionEnum.DODGE, role_name=self._role_name
            )
            use_skill = JobExecutor(
                CombatActions.use_skill(context), GameActionEnum.USE_SKILL, role_name=self._role_name
            )
            
            long_press_attack = JobExecutor(
                CombatActions.long_press_attack(context, 2100),
                GameActionEnum.LONG_PRESS_ATTACK,
                role_name=self._role_name,
            )
            ball_elimination = JobExecutor(
                CombatActions.ball_elimination(context), GameActionEnum.BALL_ELIMINATION, role_name=self._role_name
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
            if CombatActions.check_status(context, "检查阶段p1_深谣",self._role_name):
                print("p1阶段")
                if CombatActions.check_status(context, "检查u1_深谣",self._role_name):
                    print("释放技能")
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        use_skill.execute()  # 像泡沫一样,消散吧
                else:
                    print("没有技能")
                    if CombatActions.check_status(context, "检查核心被动1_深谣",self._role_name):
                        print("p1核心被动1")
                        start_time = time.time()
                        while time.time() - start_time < 1:
                            time.sleep(0.1)
                            context.tasker.controller.post_click(1224, 513).wait()  # 从我眼前,消失
                        time.sleep(0.1)
                        dodge.execute()  # 闪避
                        time.sleep(0.2)
                        context.tasker.controller.post_click(1112, 510).wait()  # 消球 
                    elif CombatActions.check_status(context, "检查核心被动2_深谣",self._role_name):
                        print("p1核心被动2")
                        start_time = time.time()
                        while time.time() - start_time < 1:
                            time.sleep(0.1)
                            context.tasker.controller.post_click(1218, 506).wait()  # 从我眼前,消失
                    else:
                        print("没有核心被动")
                        start_time = time.time()
                        while time.time() - start_time < 2:
                            time.sleep(0.1)
                            attack.execute()  # 攻击
                        context.tasker.controller.post_click(1104, 502).wait()

            elif CombatActions.check_status(context, "检查阶段p2_深谣",self._role_name):
                print("p2阶段")
                if CombatActions.check_status(context, "检查u2_深谣",self._role_name):
                    print("释放技能")
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        context.tasker.controller.post_click(1218, 506).wait()  # 滚出这里
                    context.tasker.controller.post_swipe(1199, 635, 1199, 635, 1500).wait()  # 毁灭吧
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        context.tasker.controller.post_click(924, 631).wait()  # 沉没在,这片海底
                else:
                    print("没有技能")
                    if CombatActions.check_status(context, "检查核心被动2_深谣",self._role_name):
                        print("p2核心被动2")
                        start_time = time.time()
                        while time.time() - start_time < 1:
                            time.sleep(0.1)
                            context.tasker.controller.post_click(1218, 506).wait()  # 滚出这里
                            context.tasker.controller.post_swipe(1199, 635, 1199, 635, 1000).wait()  # 毁灭吧
                    elif CombatActions.check_status(context, "检查p2动能条_深谣",self._role_name):
                        start_time = time.time()
                        while time.time() - start_time < 1:
                            time.sleep(0.1)
                            context.tasker.controller.post_click(1218, 506).wait()  # 滚出这里
                            context.tasker.controller.post_swipe(1199, 635, 1199, 635, 1000).wait()  # 毁灭吧
                    else:
                        print("没有核心被动")
                        start_time = time.time()
                        while time.time() - start_time < 2:
                            time.sleep(0.1)
                            attack.execute()  # 攻击
                        context.tasker.controller.post_click(1104, 502).wait()
            return CustomAction.RunResult(success=True)
        except Exception as e:
            logging.getLogger(f"{self._role_name}_Job").exception(str(e))
            return CustomAction.RunResult(success=False)
