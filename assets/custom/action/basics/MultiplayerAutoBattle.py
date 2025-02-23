import time
from typing import Dict, Optional

from maa.context import Context
from maa.custom_action import CustomAction


# 角色名称到动作的映射表
ROLE_ACTIONS = {
    "露娜·终焉": "Oblivion",
    "比安卡·深痕": "Stigmata",
    "拉弥亚·深谣": "LostLullaby",
    "露西亚·深红囚影": "CrimsonWeave",
    "露西亚·誓焰": "Pyroath",
}


class MultiplayerAutoBattle(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        try:
            image = context.tasker.controller.post_screencap().wait().get()
            # 检查当前角色
            for role_name, action in ROLE_ACTIONS.items():
                result = context.run_recognition(f"检查{role_name}", image)
                if result is not None:
                    # 覆写角色动作
                    context.override_pipeline({"角色特有战斗": {"action": "Custom", "custom_action": action}})
                    for _ in range(5):
                        context.run_task("角色特有战斗")
                    break  # 找到后立即跳出循环
            else:
                # 如果没有找到任何匹配的角色，记录错误信息
                print(f"未识别到任何已知角色: {list(ROLE_ACTIONS.keys())}")
                return CustomAction.RunResult(success=False)
        except Exception as e:
            # 捕获异常并记录错误信息
            print(f"执行MultiplayerAutoBattle时发生错误: {e}")
            return CustomAction.RunResult(success=False)
        
        return CustomAction.RunResult(success=True)
