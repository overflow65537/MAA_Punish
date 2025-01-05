from maa.context import Context
from maa.custom_action import CustomAction
import time


class CrimsonWeave(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        image = context.tasker.controller.post_screencap().wait().get()
        uskill_status = context.run_recognition("检查短刀", image)
        if uskill_status:
            print("短刀流程")
            blue_ball = context.run_recognition("检查蓝", image)
            if blue_ball:  # 检查是否有蓝球
                x, y = (
                    blue_ball.best_result.box[0] + blue_ball.best_result.box[2] // 2,
                    blue_ball.best_result.box[1] + blue_ball.best_result.box[3] // 2,
                )
                context.tasker.controller.post_click(x, y).wait()
                print("蓝球")
            image = context.tasker.controller.post_screencap().wait().get()
            u1 = context.run_recognition("检查u1", image)
            if u1:  # 检查一段大招
                context.tasker.controller.post_click(910, 631).wait()
                return CustomAction.RunResult(success=True)
            print("没有大招")
        else:
            print("长刀流程")
            red_ball = context.run_recognition("检查红", image)

            if red_ball:  # 检查是否有红球
                x, y = (
                    red_ball.best_result.box[0] + red_ball.best_result.box[2] // 2,
                    red_ball.best_result.box[1] + red_ball.best_result.box[3] // 2,
                )
                context.tasker.controller.post_click(x, y).wait()
                time.sleep(0.5)
                context.tasker.controller.post_click(x, y).wait()
                print("红球")
                return CustomAction.RunResult(success=True)

            yellow_ball = context.run_recognition("检查黄", image)
            if yellow_ball:  # 检查是否有黄球
                x, y = (
                    yellow_ball.best_result.box[0]
                    + yellow_ball.best_result.box[2] // 2,
                    yellow_ball.best_result.box[1]
                    + yellow_ball.best_result.box[3] // 2,
                )
                context.tasker.controller.post_click(x, y).wait()
                time.sleep(0.5)
                context.tasker.controller.post_click(x, y).wait()
                print("黄球")
                return CustomAction.RunResult(success=True)

            non_light_value = context.run_recognition("检查600", image)  # 无光值600
            if non_light_value:  # 检查无光值大于474
                print("无光值大于474")
                context.tasker.controller.post_swipe(1055, 629, 1055, 629, 2000).wait()
                time.sleep(0.5)
                context.tasker.controller.post_swipe(
                    1201, 632, 1201, 632, 2000
                ).wait()  # 登龙

                image = context.tasker.controller.post_screencap().wait().get()
                u2 = context.run_recognition("检查u2", image)
                if u2:  # 检查是否有u2
                    print("u2")
                    while u2:
                        print("点击u2")
                        image = context.tasker.controller.post_screencap().wait().get()
                        u2 = context.run_recognition("检查u2", image)
                        context.tasker.controller.post_click(910, 631).wait()
        # context.tasker.controller.post_touch_down(183,442,1).wait()# 按前进
        context.tasker.controller.post_click(1055, 629).wait()  # 按一下闪避
        # context.tasker.controller.post_touch_up(1)# 松开前进
        time.sleep(0.5)
        context.tasker.controller.post_click(1201, 632).wait()  # 普通攻击
        time.sleep(0.5)
        context.tasker.controller.post_click(1201, 632).wait()  # 普通攻击
        time.sleep(0.5)
        context.tasker.controller.post_click(1201, 632).wait()  # 普通攻击
        time.sleep(0.5)
        context.tasker.controller.post_click(1201, 632).wait()  # 普通攻击
        time.sleep(0.5)
        context.tasker.controller.post_click(1201, 632).wait()  # 普通攻击
        return CustomAction.RunResult(success=True)
