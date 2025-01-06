from maa.context import Context
from maa.custom_action import CustomAction
import time


class Stigmata(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        image = context.tasker.controller.post_screencap().wait().get()
        status = context.run_recognition("检查阶段_深痕", image)
        if not status:
            print("杖形态")
            value = context.run_recognition("检查核心被动_深痕", image)
            if value:
                print("核心被动")
                time.sleep(0.5)
                context.tasker.controller.post_swipe(
                    1049, 627, 1049, 627, 1250
                ).wait()  # 开启照域

                start_time = time.time()
                while time.time() - start_time < 4:
                    context.tasker.controller.post_click(1214, 512).wait()
                    context.tasker.controller.post_click(1194, 631).wait()

                image = context.tasker.controller.post_screencap().wait().get()
                u1 = context.run_recognition("检查u1_深痕", image)
                while u1:
                    print("u1")

                    context.tasker.controller.post_swipe(
                        915, 629, 915, 629, 1250
                    ).wait()  # 此刻,见证终焉之光
                    image = context.tasker.controller.post_screencap().wait().get()
                    u1 = context.run_recognition("检查u1_深痕", image)

        else:
            print("剑形态")
            context.tasker.controller.post_click(1194, 631).wait()
            image = context.tasker.controller.post_screencap().wait().get()
            u2_value = context.run_recognition("检查u2数值_深痕", image)
            if u2_value:
                print("残光值大于37")
                image = context.tasker.controller.post_screencap().wait().get()
                u2 = context.run_recognition("检查u2_深痕", image)
                while u2:
                    print("u2")
                    context.tasker.controller.post_swipe(
                        915, 629, 915, 629, 1500
                    ).wait()  # 以此宣告,噩梦的崩解
                    image = context.tasker.controller.post_screencap().wait().get()
                    u2 = context.run_recognition("检查u2_深痕", image)
        return CustomAction.RunResult(success=True)
