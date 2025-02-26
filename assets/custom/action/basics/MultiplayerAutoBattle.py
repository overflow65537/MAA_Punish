
import time
from maa.context import Context
from maa.custom_action import CustomAction
from assets.custom.action.tool import LoadSetting

# 角色名称到动作的映射表
ROLE_ACTIONS =  LoadSetting.load_role_setting()
class MultiplayerAutoBattle(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        try:
            time.sleep(0.1)
            image = context.tasker.controller.post_screencap().wait().get()
            # 检查当前角色
            for role_name, action in ROLE_ACTIONS.items():
                result = context.run_recognition(f"检查{role_name}", image)
                if result is not None:
                    # 覆写角色动作
                    context.override_pipeline({"角色特有战斗": {"action": "Custom", "custom_action": action}})
                    for _ in range(5):
                        if context.run_task("角色特有战斗").status == "success":
                            continue
                    break  # 找到后立即跳出循环
                else:
                    context.override_pipeline({"角色特有战斗": {"action": "Custom"}})
                    for _ in range(2):
                            if context.run_task("角色特有战斗").status == "success":
                                continue
                return CustomAction.RunResult(success=True)
        except Exception as e:
            # 捕获异常并记录错误信息
            print(f"执行MultiplayerAutoBattle时发生错误: {e}")
            return CustomAction.RunResult(success=False)
