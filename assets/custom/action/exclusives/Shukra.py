import logging
import sys
import time
from pathlib import Path

# 获取当前文件的绝对路径
current_file = Path(__file__).resolve()

# 定义可能的项目根目录相对路径
root_paths = [
    current_file.parent.parent.parent.parent.joinpath("MFW_resource"),
    current_file.parent.parent.parent.parent.parent.parent.joinpath("Bundles").joinpath(
        "MAA_Punish"
    ),
    current_file.parent.parent.parent.parent.parent.joinpath("assets"),
]

# 确定项目根目录
project_root = next((path for path in root_paths if path.exists()), None)
if project_root:
    if project_root == current_file.parent.parent.parent.parent.joinpath(
        "MFW_resource"
    ):
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
            "red": {"识别信号球": {"template": ["信号球\\启明_红.png"]}},
            "blue": {"识别信号球": {"template": ["信号球\\启明_蓝.png"]}},
            "yellow": {"识别信号球": {"template": ["信号球\\启明_黄.png"]}},
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
            )

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
            attack = JobExecutor(
                CombatActions.attack(context),
                GameActionEnum.ATTACK,
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
                    print(f"初次消球")
                    if target > 0:
                        time.sleep(0.1)
                        print(f"三连目标,开始二次消球")
                        CombatActions.ball_elimination_target(context, 1)()  # 单独消球
                    elif target == 0:
                        print(f"信号球空,结束")
                        break
                print(f"长按攻击")
                long_press_attack.execute()
            else:
                print(f"普攻")
                start_time = time.time()
                while time.time() - start_time < 2:
                    attack.execute()  # 攻击
                    time.sleep(0.1)
            return CustomAction.RunResult(success=True)
        except Exception as e:
            logging.getLogger(f"{self._role_name}_Job").exception(str(e))
            return CustomAction.RunResult(success=False)
