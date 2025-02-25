import json
import os

from maa.context import Context
from maa.custom_action import CustomAction


class MultiplayerAutoBattle(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        try:
             # 角色名称到动作的映射表
            with open(os.path.join(os.path.dirname(__file__), '..', 'setting.json'), 'r', encoding='utf-8') as file:
                ROLE_ACTIONS = json.load(file).get("ROLE_ACTIONS", {})
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
                context.override_pipeline({"角色特有战斗": {"action": "Custom", "custom_action": action}})
                for _ in range(2):
                        context.run_task("角色特有战斗")
                return CustomAction.RunResult(success=False)
        except Exception as e:
            # 捕获异常并记录错误信息
            print(f"执行MultiplayerAutoBattle时发生错误: {e}")
            return CustomAction.RunResult(success=False)
        
        return CustomAction.RunResult(success=True)
