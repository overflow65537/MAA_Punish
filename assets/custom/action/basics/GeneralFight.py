from maa.context import Context
from maa.custom_action import CustomAction


class GeneralFight(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        context.tasker.controller.post_click(1216, 504).wait()  # 消球
        context.tasker.controller.post_click(915, 626).wait()  # 技能
        context.tasker.controller.post_click(1202, 631).wait()  # 攻击
        return CustomAction.RunResult(success=True)
