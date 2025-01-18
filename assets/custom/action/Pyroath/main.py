from maa.context import Context
from maa.custom_action import CustomAction
import time


class Pyroath(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        image = context.tasker.controller.post_screencap().wait().get()
        if context.run_recognition("检查u1_誓焰", image):
            print("誓焰u1")
            if context.run_recognition("检查p1动能条_誓焰", image):
                print("p1动能条max")
                context.tasker.controller.post_swipe(
                    917, 631, 917, 631, 1250
                ).wait()  # 汇聚,阳炎之光

                context.tasker.controller.post_swipe(
                    1197, 636, 1197, 636, 1000
                )  # 长按攻击
                start_time = time.time()
                while time.time() - start_time < 1:
                    time.sleep(0.1)
                    context.tasker.controller.post_click(
                        1197, 636
                    ).wait()  # 再次点击攻击
                start_time = time.time()
                while time.time() - start_time < 1:
                    time.sleep(0.1)
                    context.tasker.controller.post_click(914, 626).wait()  # 进入u3阶段

            else:
                print("p1动能条非max")
                context.tasker.controller.post_click(1103, 514).wait()
                start_time = time.time()
                while time.time() - start_time < 2:
                    time.sleep(0.1)
                    context.tasker.controller.post_click(1197, 636).wait()

        elif context.run_recognition("检查u2_誓焰", image):
            print("誓焰u2")
            context.tasker.controller.post_click(914, 626).wait()  # 进入u3阶段
            if context.run_recognition("检查p1动能条_誓焰", image):
                print("p2动能条max")
                if context.run_recognition("检查u2_誓焰", image):
                    context.tasker.controller.post_swipe(
                        1197, 636, 1197, 636, 1000
                    )  # 长按攻击
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        context.tasker.controller.post_click(
                            1197, 636
                        ).wait()  # 再次点击攻击
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        context.tasker.controller.post_click(1108, 518).wait() # 黄球
                        context.tasker.controller.post_click(1197, 636).wait() # 攻击
                        context.tasker.controller.post_click(914, 626).wait() # 进入u3阶段

            else:
                if context.run_recognition("检查u2max_誓焰", image):
                    
                    
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        context.tasker.controller.post_click(1108, 518).wait() # 黄球
                        context.tasker.controller.post_click(1197, 636).wait() # 攻击
                        context.tasker.controller.post_click(
                            916, 628
                        ).wait()  # 进入u3阶段
                        
                        return CustomAction.RunResult(success=True)
                print("p2动能条非max")
                context.tasker.controller.post_click(1103, 514).wait()
                start_time = time.time()
                while time.time() - start_time < 2:
                    time.sleep(0.1)
                    context.tasker.controller.post_click(1197, 636).wait()
                    

        elif context.run_recognition("检查u3_誓焰", image):
            print("誓焰u3")
            if context.run_recognition("检查p1动能条_誓焰", image):
                print("p3动能条max")
                context.tasker.controller.post_swipe(1197, 636, 1197, 636, 4000)
                start_time = time.time()
                while time.time() - start_time < 1:
                    time.sleep(0.1)
                    context.tasker.controller.post_click(
                        916, 628
                    ).wait()  # 越过迷雾,与深渊
            else:
                print("p3动能条非max")
                start_time = time.time()
                while time.time() - start_time < 2:
                    time.sleep(0.1)
                    context.tasker.controller.post_click(1197, 636).wait()
        else:
            context.tasker.controller.post_click(914, 626).wait()

        return CustomAction.RunResult(success=True)
