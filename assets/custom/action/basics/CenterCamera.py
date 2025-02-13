from maa.context import Context
from maa.custom_action import CustomAction
import time


class CenterCamera(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        image=context.tasker.controller.post_screencap().wait().get()
        if argv.custom_action_param == '{"tower":true}':
            origin_pos=context.run_recognition("战斗地块_寒境曙光",image)
            x, y = (
                        origin_pos.best_result.box[0],
                        origin_pos.best_result.box[1],
                    )
            context.tasker.controller.post_swipe(x, y, 764,334, 2000).wait()
            time.sleep(1)
            context.tasker.controller.post_click(100,100).wait()
            time.sleep(1)
            return CustomAction.RunResult(success=True)
        else:
            origin_pos=context.run_recognition("重置镜头",image)
            x, y = (
                        origin_pos.best_result.box[0],
                        origin_pos.best_result.box[1],
                    )
            context.tasker.controller.post_swipe(x, y, 1052, 342, 2000).wait()
            time.sleep(1)
            context.tasker.controller.post_click(100,100).wait()
            time.sleep(1)
            return CustomAction.RunResult(success=True)

