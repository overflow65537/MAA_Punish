from maa.context import Context
from maa.custom_action import CustomAction
import time


class LostLullaby(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        print("开始")
        image = context.tasker.controller.post_screencap().wait().get()
        if context.run_recognition("检查阶段p1_深谣", image):
            print("p1阶段")
            if context.run_recognition("检查u1_深谣", image):
                print("释放技能")
                start_time = time.time()
                while time.time() - start_time < 1:
                    time.sleep(0.1)
                    context.tasker.controller.post_click(
                        924, 631
                    ).wait()  # 像泡沫一样,消散吧
            else:
                print("没有技能")
                if context.run_recognition("检查核心被动1_深谣", image):
                    print("p1核心被动1")
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        context.tasker.controller.post_click(
                            1224, 513
                        ).wait()  # 从我眼前,消失
                    time.sleep(0.2)
                    context.tasker.controller.post_click(1053, 631).wait()  # 闪避
                    time.sleep(0.2)
                    context.tasker.controller.post_click(1112, 510).wait()  # 消球
                elif context.run_recognition("检查核心被动2_深谣", image):
                    print("p1核心被动2")
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        context.tasker.controller.post_click(
                            1218, 506
                        ).wait()  # 从我眼前,消失
                else:
                    print("没有核心被动")
                    start_time = time.time()
                    while time.time() - start_time < 2:
                        time.sleep(0.1)
                        context.tasker.controller.post_click(
                            1197, 636
                        ).wait()  #攻击
                    context.tasker.controller.post_click(1104, 502).wait()

        elif context.run_recognition("检查阶段p2_深谣", image):
            print("p2阶段")
            if context.run_recognition("检查u2_深谣", image):
                print("释放技能")
                start_time = time.time()
                while time.time() - start_time < 1:
                    time.sleep(0.1)
                    context.tasker.controller.post_click(1218, 506).wait()  # 滚出这里
                context.tasker.controller.post_swipe(
                    1199, 635, 1199, 635, 1500
                ).wait()  # 毁灭吧
                start_time = time.time()
                while time.time() - start_time < 1:
                    time.sleep(0.1)
                    context.tasker.controller.post_click(
                        924, 631
                    ).wait()  # 沉没在,这片海底
            else:
                print("没有技能")
                if context.run_recognition("检查核心被动2_深谣", image):
                    print("p2核心被动2")
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        context.tasker.controller.post_click(
                            1218, 506
                        ).wait()  # 滚出这里
                        context.tasker.controller.post_swipe(
                            1199, 635, 1199, 635, 1000
                        ).wait()  # 毁灭吧
                elif context.run_recognition("检查p2动能条_深谣", image):
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        time.sleep(0.1)
                        context.tasker.controller.post_click(
                            1218, 506
                        ).wait()  # 滚出这里
                        context.tasker.controller.post_swipe(
                            1199, 635, 1199, 635, 1000
                        ).wait()  # 毁灭吧
                else:
                    print("没有核心被动")
                    start_time = time.time()
                    while time.time() - start_time < 2:
                        time.sleep(0.1)
                        context.tasker.controller.post_click(
                            1197, 636
                        ).wait()  #攻击
                    context.tasker.controller.post_click(1104, 502).wait()
        print("结束")
        return CustomAction.RunResult(success=True)
