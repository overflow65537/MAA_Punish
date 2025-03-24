from maa.context import Context
from maa.custom_action import CustomAction
import random



class ArrangeSignalBalls(CustomAction):
    
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        def determine_elimination(ball_list, target):
            """优化后的消球逻辑（考虑None分布特性）"""
            # 寻找有效球区域（跳过首尾None）
            start = 0
            end = len(ball_list) - 1
            
            # 跳过开头的单个None（如果存在）
            if ball_list[0] is None:
                start = 1
                
            # 跳过末尾的连续None
            while end > start and ball_list[end] is None:
                end -= 1

            # 提取有效区间
            valid_zone = ball_list[start:end+1]
            
            # 第一优先级：目标三连
            for i in range(len(valid_zone)-2):
                if valid_zone[i:i+3] == [target]*3:
                    return start + i + 1  # 映射回原始索引

            # 第二优先级：形成目标连击
            for i in range(len(valid_zone)):
                temp = valid_zone[:i] + valid_zone[i+1:]
                if any(temp[j]==temp[j+1]==target for j in range(len(temp)-1)):
                    return start + i

            # 第三优先级：任意三连（利用有效区间减少遍历）
            for i in range(len(valid_zone)-2):
                if valid_zone[i] and valid_zone[i] == valid_zone[i+1] == valid_zone[i+2]:
                    return start + i + 1

            # 第四优先级：随机选择有效球（优先有效区间）
            valid = [start+i for i, x in enumerate(valid_zone) if x]
            return random.choice(valid) if valid else False

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

        override = (argv.custom_action_param)
        image = context.tasker.controller.post_screencap().wait().get()
        ball_list = [None,None,None,None,None,None,None,None]
        red_ball = context.run_recognition("技能_能量条", image,override.get("red"))
        if red_ball:
            for i in red_ball.filterd_results:
                result = Analyze_signal_balls(i.box) 
                if result is not False:
                    ball_list[result] = "r"

        blue_ball = context.run_recognition("技能_能量条", image,override.get("blue"))
        if blue_ball:
            for i in blue_ball.filterd_results:
                result = Analyze_signal_balls(i.box)
                if result is not False:
                    ball_list[result] = "b"
        yellow_ball = context.run_recognition("技能_能量条", image,override.get("yellow"))
        if yellow_ball:
            for i in yellow_ball.filterd_results:
                result = Analyze_signal_balls(i.box)
                if result is not False:
                    ball_list[result] = "y"
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
        target  = determine_elimination(ball_list, "r")
        x,y = balls[target][0],balls[target][1]
        return lambda: context.tasker.controller.post_click(x,y).wait()  
        

        