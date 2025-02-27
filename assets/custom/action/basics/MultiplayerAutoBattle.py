import time

from maa.context import Context
from maa.custom_action import CustomAction
from assets.custom.action.tool.LoadSetting import ROLE_ACTIONS


class MultiplayerAutoBattle(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        try:
            image = context.tasker.controller.post_screencap().wait().get()

            # 检查当前角色
            recognized_role = None
            for role_name, action in ROLE_ACTIONS.items():
                result = context.run_recognition(f"检查{role_name}", image)
                if result is not None:
                    recognized_role = {"action": "Custom", "custom_action": action}
                    break

            if recognized_role:
                context.override_pipeline({"角色特有战斗": recognized_role})
                max_battles = 2
            else:
                context.override_pipeline({"通用战斗模式": {}})
                max_battles = 1

            n = 0
            while n < max_battles:
                context.run_task("角色特有战斗" if recognized_role else "通用战斗模式")
                n += 1

            return CustomAction.RunResult(success=True)
        except Exception as e:
            # 捕获异常并记录错误信息
            print(f"执行MultiplayerAutoBattle时发生错误: {e}")
            return CustomAction.RunResult(success=False)
