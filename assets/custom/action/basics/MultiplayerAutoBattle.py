import time
from typing import Dict



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

        image = context.tasker.controller.post_screencap().wait().get()
        # 检查当前角色
        for key, value in ROLE_ACTIONS.items():
            result = context.run_recognition(f"检查{key}", image,)
            if result is not None:
                # 覆写角色动作
                context.override_pipeline({"角色特有战斗_1": {"action": "Custom", "custom_action": value}})

                context.run_task("角色特有战斗_1")
                context.run_task("角色特有战斗_1")
                context.run_task("角色特有战斗_1")
                context.run_task("角色特有战斗_1")
                break  # 找到后立即跳出循环
        
        # 切人
        time.sleep(0.1)
        context.tasker.controller.post_click(1208, 154).wait()
        context.tasker.controller.post_click(1208, 272).wait()        
        return CustomAction.RunResult(success=True)
