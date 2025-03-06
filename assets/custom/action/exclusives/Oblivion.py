import sys
from pathlib import Path

# 获取当前文件的绝对路径
current_file = Path(__file__).resolve()

# 定义可能的项目根目录相对路径
root_paths = [
    current_file.parent.parent.parent.parent.joinpath("MFW_resource"),
    current_file.parent.parent.parent.parent.parent.parent.joinpath("Bundles").joinpath("MAA_Punish"),
    current_file.parent.parent.parent.parent.parent.joinpath("assets")
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
from maa.context import Context
from maa.custom_action import CustomAction

# 还需识别能量条数字，大招图标
class Oblivion(CustomAction):
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
            # 初始残月值检查
            if self.__check_moon(context):
                print("[状态] 残月值满")
                # 长按普攻
                long_press_attack = JobExecutor(
                    CombatActions.long_press_attack(context, 2000), GameActionEnum.LONG_PRESS_ATTACK
                ,role_name="Oblivion")
                if not long_press_attack.execute():
                    return CustomAction.RunResult(success=False)

                # # 释放大招
                use_skill = JobExecutor(CombatActions.use_skill(context),GameActionEnum.USE_SKILL,role_name="Oblivion")
                if not use_skill.execute():
                    return CustomAction.RunResult(success=False)

                return CustomAction.RunResult(success=True)

            # 消球操作
            print("[阶段] 执行消球")
            for i in range(2):  # 最多尝试2次消球
                ball_elimination = JobExecutor(CombatActions.ball_elimination(context), GameActionEnum.BALL_ELIMINATION,role_name="Oblivion")
                if ball_elimination.execute():
                    continue
                else:
                    print(f"[状态] 消球失败，尝试第{i+1}次消球")
                    return CustomAction.RunResult(success=False)
            return CustomAction.RunResult(success=True)
        except Exception as e:
            print(f"[严重错误] 执行流程中断: {str(e)}")
            return CustomAction.RunResult(success=False)
