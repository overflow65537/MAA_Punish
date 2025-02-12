from maa.context import Context
from maa.custom_action import CustomAction


class CenterCamera(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        image=context.tasker.controller.post_screencap().wait().get()
        origin_pos=context.run_recognition("回到boss界面_操作",image)
        x, y = (
                    origin_pos.best_result.box[0],
                    origin_pos.best_result.box[1],
                )
        context.tasker.controller.post_swipe(x, y, 1052, 342, 2000).wait()
        
        return CustomAction.RunResult(success=True)
