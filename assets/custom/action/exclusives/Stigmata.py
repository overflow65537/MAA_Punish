from maa.context import Context
from maa.custom_action import CustomAction
import time


class Stigmata(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        image = context.tasker.controller.post_screencap().wait().get()
        if not context.run_recognition("检查阶段_深痕", image):
            print("杖形态")
            if context.run_recognition("检查核心被动_深痕", image):
                print("核心被动")
                time.sleep(0.5)
                context.tasker.controller.post_swipe(
                    1049, 627, 1049, 627, 1250
                ).wait()  # 开启照域

                start_time = time.time()
                while time.time() - start_time < 3:
                    context.tasker.controller.post_click(1214, 512).wait()
                    time.sleep(0.1)
                    context.tasker.controller.post_click(1194, 631).wait()
                    time.sleep(0.1)

                image = context.tasker.controller.post_screencap().wait().get()
                if context.run_recognition("检查u1_深痕", image):
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        print("u1")
                        context.tasker.controller.post_swipe(
                            915, 629, 915, 629, 1250
                        ).wait()  # 此刻,见证终焉之光
                        image = context.tasker.controller.post_screencap().wait().get()

        else:
            print("剑形态")
            start_time = time.time()
            while time.time() - start_time < 1:
                context.tasker.controller.post_click(1194, 631).wait()
                time.sleep(0.2)
            image = context.tasker.controller.post_screencap().wait().get()
            if context.run_recognition("检查u2数值_深痕", image):
                print("残光值大于90")
                image = context.tasker.controller.post_screencap().wait().get()
                if context.run_recognition("检查u2_深痕", image):
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        print("u2")
                        context.tasker.controller.post_swipe(
                            915, 629, 915, 629, 1500
                        ).wait()  # 以此宣告,噩梦的崩解
                        image = context.tasker.controller.post_screencap().wait().get()
                
        return CustomAction.RunResult(success=True)
