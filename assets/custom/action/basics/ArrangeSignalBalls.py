from maa.context import Context
from maa.custom_action import CustomAction
import random


class ArrangeSignalBalls(CustomAction):

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        def find_optimal_ball(ball_list, target):
            """根据信号球规则寻找最优操作目标"""
            # 第一优先级：寻找目标色且左右相同的元素
            for i in range(1, 7):  # 跳过首尾的特殊情况
                if ball_list[i] and ball_list[i] == target or (target == 'any' and ball_list[i]):
                    left = ball_list[i-1] if i > 0 else None
                    right = ball_list[i+1] if i < 7 else None
                    if (left == ball_list[i] and right == ball_list[i]) and left is not None and right is not None:
                        print("第一优先级：寻找目标色且左右相同的元素")
                        return i + 1  # 返回从1开始的序号

            # 第二优先级：寻找能形成目标三连的消除位置
            for i in range(8):
                if ball_list[i] is None:
                    continue
                temp = ball_list[:i] + ball_list[i+1:]
                for j in range(len(temp)-2):
                    if target != 'any' and temp[j:j+3] == [target]*3:
                        print("第二优先级：寻找能形成目标三连的消除位置")
                        return -(i + 1)  # 返回负数序号
                    elif target == 'any' and temp[j] and temp[j] == temp[j+1] == temp[j+2]:
                        print("第二优先级：寻找能形成任意三连的消除位置")
                        return -(i + 1)

            # 第三优先级：寻找能形成任意三连的消除位置
            for i in range(8):
                if ball_list[i] is None:
                    continue
                temp = ball_list[:i] + ball_list[i+1:]
                for j in range(len(temp)-2):
                    if temp[j] and temp[j] == temp[j+1] == temp[j+2]:
                        print("第三优先级：寻找能形成任意三连的消除位置")
                        return -(i + 1)

            # 第四优先级：随机选择非None元素
            valid = [i+1 for i, x in enumerate(ball_list) if x is not None]
            if valid:
                print("第四优先级：随机选择非None元素")
                return -random.choice(valid)
            print("未找到最优操作目标")
            return 0

        def Analyze_signal_balls(box):
            balls = [
                [1220, 500],
                [1111, 500],
                [1003, 500],
                [894, 500],
                [786, 500],
                [677, 500],
                [569, 500],
                [460, 500],
            ]
            x, y, w, h = box
            for i, ball in enumerate(balls):
                if x <= ball[0] <= x + w and y <= ball[1] <= y + h:
                    return i
            return False

        override = {
            "red": {"识别信号球": {"template": ["信号球\\启明_红.png"]}},
            "blue": {"识别信号球": {"template": ["信号球\\启明_蓝.png"]}},
            "yellow": {"识别信号球": {"template": ["信号球\\启明_黄.png"]}},
        }
        image = context.tasker.controller.post_screencap().wait().get()
        ball_list = [None, None, None, None, None, None, None, None]
        red_ball = context.run_recognition("识别信号球", image, override.get("red"))
        if red_ball:
            print(f"识别到红球{red_ball.filterd_results}")
            for i in red_ball.filterd_results:
                result = Analyze_signal_balls(i.box)
                if result is not False:
                    ball_list[result] = "r"
            print(f"红球结束{ball_list}")
        else:
            print("未识别到红球")

        blue_ball = context.run_recognition("识别信号球", image, override.get("blue"))
        if blue_ball:
            print(f"识别到蓝球{blue_ball.filterd_results}")
            for i in blue_ball.filterd_results:
                result = Analyze_signal_balls(i.box)
                if result is not False:
                    ball_list[result] = "b"
            print(f"蓝球结束{ball_list}")
        else:
            print("未识别到蓝球")
        yellow_ball = context.run_recognition(
            "识别信号球", image, override.get("yellow")
        )
        if yellow_ball:
            print(f"识别到黄球{yellow_ball.filterd_results}")
            for i in yellow_ball.filterd_results:
                result = Analyze_signal_balls(i.box)
                if result is not False:
                    ball_list[result] = "y"
            print(f"黄球结束{ball_list}")
        else:
            print("未识别到黄球")
        balls = [
            [1220, 500],
            [1111, 500],
            [1003, 500],
            [894, 500],
            [786, 500],
            [677, 500],
            [569, 500],
            [460, 500],
        ]
        target = find_optimal_ball(ball_list, "r")
        print(f"目标球为{target}")
        if target is False:
            return CustomAction.RunResult(success=True)
        """x, y = balls[target][0], balls[target][1]
        context.tasker.controller.post_click(x, y).wait()"""
        return CustomAction.RunResult(success=True)
