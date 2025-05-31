# Copyright (c) 2024-2025 MAA_Punish
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
MAA_Punish
MAA_Punish 肉鸽4重置镜头
作者:HCX0426
"""

import logging
from maa.context import Context
from maa.custom_action import CustomAction
from maa.define import RecognitionDetail
import time


class CombatActions(CustomAction):
    """通用战斗"""

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        print("通用战斗")
        try:
            self.lens_lock(context)()
            self.use_skill(context)()
            self.ball_elimination_second(context)()
            now_time = time.time()
            while time.time() - now_time < 2:
                self.attack(context)()
                time.sleep(0.1)
            return CustomAction.RunResult(success=True)
        except Exception as e:
            print(f"通用战斗异常: {str(e)}")
            return CustomAction.RunResult(success=False)

    @staticmethod
    def attack(context: Context):
        """攻击"""
        return lambda: context.tasker.controller.post_click(1197, 636).wait()

    @staticmethod
    def dodge(context: Context):
        """闪避"""
        return lambda: context.tasker.controller.post_click(1052, 633).wait()

    @staticmethod
    def use_skill(context: Context):
        """技能"""
        return lambda: context.tasker.controller.post_click(915, 626).wait()

    @staticmethod
    def ball_elimination(context: Context):
        """消球"""
        return lambda: context.tasker.controller.post_click(
            1216, 518
        ).wait()  # 消第一个球

    @staticmethod
    def ball_elimination_second(context: Context):
        """消球2"""
        return lambda: context.tasker.controller.post_click(
            1097, 510
        ).wait()  # 消第二个球

    @staticmethod
    def ball_elimination_three(context: Context):
        """消球3"""
        return lambda: context.tasker.controller.post_click(
            999, 518
        ).wait()  # 消第三个球

    @staticmethod
    def ball_elimination_target(context: Context, target: int = 2):
        """指定消球目标,从1开始,默认2"""
        target = abs(target) - 1
        BALL_POSITIONS = [
            (1220, 500),
            (1111, 500),
            (1003, 500),
            (894, 500),
            (786, 500),
            (677, 500),
            (569, 500),
            (460, 500),
        ]
        print(f"消球目标: {BALL_POSITIONS[target][0]},{BALL_POSITIONS[target][1]}")
        return lambda: context.tasker.controller.post_click(
            BALL_POSITIONS[target][0], BALL_POSITIONS[target][1]
        ).wait()

    @staticmethod
    def trigger_qte(context: Context, target: int = 1):
        """触发QTE/换人"""
        if target not in (1, 2):
            raise ValueError("target 参数必须为 1 或 2")
        elif target == 1:
            return lambda: context.tasker.controller.post_click(1208, 154).wait()
        elif target == 2:
            return lambda: context.tasker.controller.post_click(1208, 265).wait()

    @staticmethod
    def trigger_qte_first(context: Context):
        """1-触发QTE/换人"""
        return lambda: context.tasker.controller.post_click(1208, 154).wait()

    @staticmethod
    def trigger_qte_second(context: Context):
        """2-触发QTE/换人"""
        return lambda: context.tasker.controller.post_click(1208, 265).wait()

    @staticmethod
    def long_press_attack(context: Context, time: int = 1000):
        """长按攻击"""
        return lambda: context.tasker.controller.post_swipe(
            1193, 633, 1198, 638, time
        ).wait()

    @staticmethod
    def long_press_dodge(context: Context, time: int = 1000):
        """长按闪避"""
        return lambda: context.tasker.controller.post_swipe(
            1052, 633, 1198, 638, time
        ).wait()

    @staticmethod
    def long_press_skill(context: Context, time: int = 1000):
        """长按技能"""
        return lambda: context.tasker.controller.post_swipe(
            915, 626, 915, 634, time
        ).wait()

    @staticmethod
    def lens_lock(context: Context):
        """镜头锁定"""
        return lambda: context.tasker.controller.post_click(1108, 383).wait()

    @staticmethod
    def auxiliary_machine(context: Context):
        """辅助机"""
        return lambda: context.tasker.controller.post_click(1214, 387).wait()

    @staticmethod
    def check_status(
        context: Context, node: str, role_name: str, pipeline_override: dict = {}
    ):
        """检查状态"""
        try:
            logger = logging.getLogger(f"{role_name}_Job")
            # 获取截图
            image = context.tasker.controller.post_screencap().wait().get()
            # 识别并返回结果
            result = context.run_recognition(node, image, pipeline_override)
            if result:
                logger.info(node + ":True")

            else:
                logger.info(node + ":False")
            return result
        except Exception as e:
            logger.exception(node + ":" + str(e))
            return False

    @staticmethod
    def check_Skill_energy_bar(context: Context, role_name: str) -> bool:
        """检查技能能量条"""
        try:
            logger = logging.getLogger(f"{role_name}_Job")
            # 获取截图
            image = context.tasker.controller.post_screencap().wait().get()
            # 识别并返回结果
            if context.run_recognition("技能_能量条", image):
                logger.info("检查技能_能量条:True")
                return True
            else:
                logger.info("检查技能_能量条:False")
                return False
        except Exception as e:
            logger.exception("检查技能_能量条:" + str(e))
            return False

    @staticmethod
    def Arrange_Signal_Balls(context: Context, target_ball: str, template: dict) -> int:
        """
        自动消球逻辑
        Args:
            context (Context): 上下文
            target_ball (str): 目标球颜色 "red", "blue", "yellow", "any"
            template (dict): 模板字典，格式为：
                {
                    "red": {"识别信号球": {"template": ["信号球/启明_红.png"]}},
                    "blue": {"识别信号球": {"template": ["信号球/启明_蓝.png"]}},
                    "yellow": {"识别信号球": {"template": ["信号球/启明_黄.png"]}}
                }

        Returns:
            int: 消球目标位置，从1开始，0表示无效操作,负数代表消球了,但不是三消

        """
        BALL_POSITIONS = [
            (1220, 500),
            (1111, 500),
            (1003, 500),
            (894, 500),
            (786, 500),
            (677, 500),
            (569, 500),
            (460, 500),
        ]

        def analyze_position(box) -> int:
            """分析信号球位置"""
            x, y, w, h = box
            for idx, (pos_x, pos_y) in enumerate(BALL_POSITIONS):
                if x <= pos_x <= x + w and y <= pos_y <= y + h:
                    return idx
            return -1

        def detect_balls(image) -> list:
            """统一处理信号球识别"""
            ball_status = [None] * 8
            for color in ["red", "blue", "yellow"]:
                result = context.run_recognition(
                    "识别信号球", image, template.get(color)
                )
                print(f"识别到{color}球: {result.filterd_results if result else '无'}")
                if result:
                    for item in result.filterd_results:
                        if (pos := analyze_position(item.box)) != -1:
                            ball_status[pos] = color
            print(f"信号球状态: {ball_status}")
            return ball_status

        def _find_optimal_ball(ball_list: list, target: str) -> int:
            """消球决策逻辑"""
            last_non_none_index = next(
                (i for i, x in enumerate(reversed(ball_list)) if x is not None), None
            )
            valid_length = (
                len(ball_list) - last_non_none_index
                if last_non_none_index is not None
                else 0
            )

            print(f"有效长度: {valid_length}")

            if valid_length == 0:
                print("未找到有效操作")
                return 0

            is_any = target == "any"

            # 按优先级顺序检查
            if result := _check_triple_direct(ball_list, valid_length, is_any, target):
                return result

            if result := _check_combo_opportunity(
                ball_list, valid_length, is_any, target
            ):
                return result

            if result := _check_any_triple(ball_list):
                return result

            return _select_non_empty(ball_list)

        def _check_triple_direct(
            ball_list: list, valid_length: int, is_any: bool, target: str
        ) -> int:
            """检查直接三连"""
            for i in range(valid_length - 2):
                if (
                    is_any and ball_list[i] == ball_list[i + 1] == ball_list[i + 2]
                ) or (
                    not is_any
                    and ball_list[i] == target
                    and ball_list[i + 1] == target
                    and ball_list[i + 2] == target
                ):
                    print(f"第一优先级：{'任意' if is_any else '目标'}三连消除")
                    return i + 1
            return 0

        def _check_combo_opportunity(
            ball_list: list, valid_length: int, is_any: bool, target: str
        ) -> int:
            """检查连击机会"""
            candidate = 0
            for i in [
                idx for idx, x in enumerate(ball_list[:valid_length]) if x is not None
            ]:
                temp = ball_list[:i] + ball_list[i + 1 :]
                for j in range(min(len(temp) - 1, valid_length - 1)):
                    if j <= len(temp) - 3:
                        if (is_any and temp[j] == temp[j + 1] == temp[j + 2]) or (
                            not is_any and temp[j : j + 3] == [target] * 3
                        ):
                            print(
                                f"第二优先级：可形成{'任意' if is_any else '目标'}三连"
                            )
                            return -(i + 1)

                    if (is_any and temp[j] == temp[j + 1]) or (
                        not is_any and temp[j] == target and temp[j + 1] == target
                    ):
                        print(f"第二优先级：可形成{'任意' if is_any else '目标'}二连")
                        candidate = -(i + 1)
            return candidate

        def _check_any_triple(ball_list: list) -> int:
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

        def _select_non_empty(ball_list: list) -> int:
            """选择非空元素"""
            return -2 if ball_list[0] is None else -1

        # 主逻辑流程
        try:
            image = context.tasker.controller.post_screencap().wait().get()
            ball_list = detect_balls(image)
            target = _find_optimal_ball(ball_list, target_ball)
            print(f"最终目标球: {target}")
            return target
        except Exception as e:
            print(f"消球决策异常: {str(e)}")
            return 0
