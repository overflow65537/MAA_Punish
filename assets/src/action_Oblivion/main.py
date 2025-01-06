from maa.context import Context
from maa.custom_action import CustomAction


class Oblivion(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        image = context.tasker.controller.post_screencap().wait().get()
        value = context.run_recognition("检查残月值_终焉", image) 
        if value:
            print("残月值满")
            context.tasker.controller.post_swipe(1193,633, 1193,633, 1000).wait()
        context.tasker.controller.post_click(915, 626).wait()  # 技能
        context.tasker.controller.post_click(1216, 504).wait()  # 消
        context.tasker.controller.post_click(1202, 631).wait()  # 攻击
        
        return CustomAction.RunResult(success=True)
