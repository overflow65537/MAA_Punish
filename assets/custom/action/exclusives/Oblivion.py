import sys
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
    print(f"项目根目录: {project_root}")
else:
    print("[错误] 找不到项目根目录")

# 添加项目根目录到sys.path
sys.path.append(str(project_root))


from custom.action.basics import CombatActions
from custom.action.tool import JobExecutor
from custom.action.tool.Enum import GameActionEnum
from custom.action.tool.LoadSetting import ROLE_ACTIONS
from maa.context import Context
from maa.custom_action import CustomAction


# 还需识别能量条数字，大招图标
class Oblivion(CustomAction):
    def __init__(self):
        super().__init__()
        for name, action in ROLE_ACTIONS.items():
            if action == self.__class__.__name__:
                self._role_name = name

    def __check_moon(self, context: Context) -> bool:
        """检查残月值"""
        try:
            # 获取截图
            image = context.tasker.controller.post_screencap().wait().get()
            # 识别残月值
            if context.run_recognition("检查残月值_终焉", image):
                return True
            else:
                return False
        except Exception as e:
            print(f"[异常] 残月值检查失败: {str(e)}")
            return False

    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        try:
            use_skill = JobExecutor(
                CombatActions.use_skill(context), GameActionEnum.USE_SKILL, role_name=self._role_name
            )
            if not use_skill.execute():
                return CustomAction.RunResult(success=False)
            if self.__check_moon(context):
                long_press_attack = JobExecutor(
                    CombatActions.long_press_attack(context, 1500),
                    GameActionEnum.LONG_PRESS_ATTACK,
                    role_name=self._role_name,
                )
                if not long_press_attack.execute():
                    return CustomAction.RunResult(success=False)

                use_skill = JobExecutor(
                    CombatActions.use_skill(context), GameActionEnum.USE_SKILL, role_name=self._role_name
                )
                if not use_skill.execute():
                    return CustomAction.RunResult(success=False)
            for i in range(2):  # 最多尝试2次消球
                ball_elimination = JobExecutor(
                    CombatActions.ball_elimination(context), GameActionEnum.BALL_ELIMINATION, role_name=self._role_name
                )
                if ball_elimination.execute():
                    continue
                else:
                    return CustomAction.RunResult(success=False)

            if not self.__check_moon(context):
                long_press_attack = JobExecutor(
                    CombatActions.long_press_attack(context, 1500),
                    GameActionEnum.LONG_PRESS_ATTACK,
                    role_name=self._role_name,
                )
                if not long_press_attack.execute():
                    return CustomAction.RunResult(success=False)

                if self.__check_moon(context):
                    long_press_attack = JobExecutor(
                        CombatActions.long_press_attack(context, 1500),
                        GameActionEnum.LONG_PRESS_ATTACK,
                        role_name=self._role_name,
                    )
                    if not long_press_attack.execute():
                        return CustomAction.RunResult(success=False)

                    use_skill = JobExecutor(
                        CombatActions.use_skill(context), GameActionEnum.USE_SKILL, role_name=self._role_name
                    )
                    if not use_skill.execute():
                        return CustomAction.RunResult(success=False)

                    return CustomAction.RunResult(success=True)

            return CustomAction.RunResult(success=True)
        except Exception as e:
            print(f"[严重错误] 执行流程中断: {str(e)}")
            return CustomAction.RunResult(success=False)
