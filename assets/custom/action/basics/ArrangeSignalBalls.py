from maa.context import Context
from maa.custom_action import CustomAction


class ArrangeSignalBalls(CustomAction):
    # 常量定义
    BALL_POSITIONS = [
        (1220, 500), (1111, 500), (1003, 500),
        (894, 500), (786, 500), (677, 500),
        (569, 500), (460, 500)
    ]
    COLOR_MAPPING = {'red': 'r', 'blue': 'b', 'yellow': 'y'}

    def run(self, context: Context, argv: CustomAction.RunArg,
            role_name: str, target_ball: str, template: dict) -> CustomAction.RunResult:
        
        def analyze_position(box) -> int:
            """分析球体坐标位置"""
            x, y, w, h = box
            for idx, (pos_x, pos_y) in enumerate(self.BALL_POSITIONS):
                if x <= pos_x <= x + w and y <= pos_y <= y + h:
                    return idx
            return -1

        def detect_balls(image) -> list:
            """统一处理球体识别"""
            ball_status = [None] * 8
            for color, key in self.COLOR_MAPPING.items():
                result = context.run_recognition("识别信号球", image, template.get(color))
                print(f"识别到{color}球: {result.filterd_results if result else '无'}")
                if result:
                    for item in result.filterd_results:
                        if (pos := analyze_position(item.box)) != -1:
                            ball_status[pos] = key
            return ball_status

        # 主逻辑流程
        try:
            image = context.tasker.controller.post_screencap().wait().get()
            ball_list = detect_balls(image)
            target = self._find_optimal_ball(ball_list, target_ball)
            print(f"最终目标球: {target}")
            return target
        except Exception as e:
            print(f"消球决策异常: {str(e)}")
            return 0

    def _find_optimal_ball(self, ball_list: list, target: str) -> int:
        """消球决策逻辑"""
        valid_length = len(ball_list) - next(
            (i for i, x in enumerate(reversed(ball_list)) if x is not None), 0)
        
        if valid_length == 0:
            print("未找到有效操作")
            return 0

        is_any = target == "any"
        
        # 按优先级顺序检查
        if result := self._check_triple_direct(ball_list, valid_length, is_any, target):
            return result
            
        if result := self._check_combo_opportunity(ball_list, valid_length, is_any, target):
            return result
            
        if result := self._check_any_triple(ball_list):
            return result
            
        return self._select_non_empty(ball_list)

    def _check_triple_direct(self, ball_list: list, valid_length: int, 
                          is_any: bool, target: str) -> int:
        """检查直接三连"""
        for i in range(valid_length - 2):
            if (is_any and ball_list[i] == ball_list[i+1] == ball_list[i+2]) or \
               (not is_any and ball_list[i] == target and ball_list[i+1] == target and ball_list[i+2] == target):
                print(f"第一优先级：{'任意' if is_any else '目标'}三连消除")
                return i + 1
        return 0

    def _check_combo_opportunity(self, ball_list: list, valid_length: int,
                              is_any: bool, target: str) -> int:
        """检查连击机会"""
        candidate = 0
        for i in [idx for idx, x in enumerate(ball_list[:valid_length]) if x is not None]:
            temp = ball_list[:i] + ball_list[i + 1 :]
            for j in range(min(len(temp) - 1, valid_length - 1)):
                if j <= len(temp) - 3:
                    if (is_any and temp[j] == temp[j+1] == temp[j+2]) or \
                       (not is_any and temp[j:j+3] == [target]*3):
                        print(f"第二优先级：可形成{'任意' if is_any else '目标'}三连")
                        return -(i + 1)
                
                if (is_any and temp[j] == temp[j+1]) or \
                   (not is_any and temp[j] == target and temp[j+1] == target):
                    print(f"第二优先级：可形成{'任意' if is_any else '目标'}二连")
                    candidate = -(i + 1)
        return candidate

    def _check_any_triple(self, ball_list: list) -> int:
        """检查任意三连"""
        for i in range(len(ball_list)):
            if ball_list[i] is None:
                continue
            temp = ball_list[:i] + ball_list[i + 1 :]
            for j in range(len(temp) - 2):
                if temp[j] is not None and temp[j] == temp[j + 1] == temp[j + 2]:
                    print("第三优先级：任意三连消除")
                    return -(i + 1)
        return 0

    def _select_non_empty(self, ball_list: list) -> int:
        """选择非空元素"""
        return -2 if ball_list[0] is None else -1