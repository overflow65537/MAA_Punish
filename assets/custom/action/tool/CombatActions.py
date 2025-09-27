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
MAA_Punish 通用战斗对象
作者:HCX0426,overflow
"""


from maa.context import Context
from pathlib import Path
import time
import sys



# 获取当前文件的绝对路径
current_file = Path(__file__).resolve()
sys.path.append(str(current_file.parent.parent.parent.parent))
from custom.action.tool.LoadSetting import ROLE_ACTIONS
from custom.action.tool.logger import Logger


class CombatActions:
    """通用战斗功能"""

    COORDINATES = {
        "attack": (1197, 636),
        "dodge": (1052, 633),
        "skill": (915, 626),
        "ball_positions": [
            (1220, 500),  # 1
            (1111, 500),  # 2
            (1003, 500),  # 3
            (894, 500),  # 4
            (786, 500),  # 5
            (677, 500),  # 6
            (569, 500),  # 7
            (460, 500),  # 8
        ],
        "qte": {
            1: (1208, 154),
            2: (1208, 265),
        },
        "lens_lock": (1108, 383),
        "auxiliary_machine": (1214, 387),
    }

    def __init__(self, context: Context, role_name: str = ""):
        self.context = context
        self.logger = Logger(role_name if role_name else "CombatActions")
        self.role_name = role_name

        self.template = {}
        if role_name in ROLE_ACTIONS:
            self.template = ROLE_ACTIONS[role_name].get("skill_template", {})
        else:
            for role in ROLE_ACTIONS.values():
                if role_name == role["name"]:
                    self.template = role.get("skill_template", {})
                    break


    def attack(self):
        """攻击"""
        return self.context.tasker.controller.post_click(
            *self.COORDINATES["attack"]
        ).wait()

    def continuous_attack(self, count: int = 10, interval: int = 100) -> bool:
        """连续攻击"""
        for _ in range(count):
            self.attack()
            time.sleep(interval / 1000)
        return True

    def long_press_attack(self, duration: int = 1000):
        """长按攻击"""
        atk_x = self.COORDINATES["attack"][0]
        atk_y = self.COORDINATES["attack"][1]
        return self.context.tasker.controller.post_swipe(
            atk_x, atk_y, atk_x, atk_y, duration
        ).wait()

    def dodge(self):
        """闪避"""
        return self.context.tasker.controller.post_click(
            *self.COORDINATES["dodge"]
        ).wait()

    def long_press_dodge(self, duration: int = 1000):
        """长按闪避"""
        dodge_x = self.COORDINATES["dodge"][0]
        dodge_y = self.COORDINATES["dodge"][1]
        return self.context.tasker.controller.post_swipe(
            dodge_x, dodge_y, dodge_x, dodge_y, duration
        ).wait()

    def use_skill(self):
        """技能"""
        return self.context.tasker.controller.post_click(
            *self.COORDINATES["skill"]
        ).wait()

    def long_press_skill(self, time: int = 1000):
        """长按技能"""
        skill_x = self.COORDINATES["skill"][0]
        skill_y = self.COORDINATES["skill"][1]
        return self.context.tasker.controller.post_swipe(
            skill_x, skill_y, skill_x, skill_y, time
        ).wait()

    def ball_elimination_target(self, target: int = 2):
        """指定消球目标,从1开始,默认2"""
        target = abs(target) - 1
        ball_x = self.COORDINATES["ball_positions"][target][0]
        ball_y = self.COORDINATES["ball_positions"][target][1]
        return self.context.tasker.controller.post_click(ball_x, ball_y).wait()

    def trigger_qte(self, target: int = 1):
        """触发QTE/换人"""
        if target not in (1, 2):
            raise ValueError("target 参数必须为 1 或 2")
        elif target == 1:
            return self.context.tasker.controller.post_click(
                *self.COORDINATES["qte"][1]
            ).wait()
        elif target == 2:
            return self.context.tasker.controller.post_click(
                *self.COORDINATES["qte"][2]
            ).wait()

    def lens_lock(self):
        """镜头锁定"""
        return self.context.tasker.controller.post_click(
            *self.COORDINATES["lens_lock"]
        ).wait()

    def auxiliary_machine(self):
        """辅助机"""
        return self.context.tasker.controller.post_click(
            *self.COORDINATES["auxiliary_machine"]
        ).wait()

    def check_status(self, node: str, pipeline_override: dict = {}):
        """检查状态"""
        try:
            # 获取截图
            image = self.context.tasker.controller.post_screencap().wait().get()
            # 识别并返回结果
            result = self.context.run_recognition(node, image, pipeline_override)
            if result:
                self.logger.info(node + ":True")

            else:
                self.logger.info(node + ":False")
            return result
        except Exception as e:
            self.logger.exception(node + ":" + str(e))
            return False

    def check_Skill_energy_bar(self) -> bool:
        """检查技能能量条"""
        try:
            # 获取截图
            image = self.context.tasker.controller.post_screencap().wait().get()
            # 识别并返回结果
            if self.context.run_recognition("技能_能量条", image):
                self.logger.info("检查技能_能量条:True")
                return True
            else:
                self.logger.info("检查技能_能量条:False")
                return False
        except Exception as e:
            self.logger.exception("检查技能_能量条:" + str(e))
            return False

    def Arrange_Signal_Balls(self, target_ball: str) -> int:
        """
        自动消球逻辑
        Args:
            target_ball (str): 目标球颜色 "red", "blue", "yellow", "any"
        Returns:
            int: 消球目标位置，从1开始，0表示无效操作,负数代表可以消球,但不是三消但可能促成三消

        """
        if self.template == {}:
            self.logger.error("模板未加载")
            return 0

        def analyze_position(box) -> int:
            """分析信号球位置"""
            try:
                # 确保box可以解包为4个整数
                x, y, w, h = box
                for idx, (pos_x, pos_y) in enumerate(
                    self.COORDINATES["ball_positions"]
                ):
                    if x <= pos_x <= x + w and y <= pos_y <= y + h:
                        return idx
                return -1
            except (TypeError, ValueError) as e:
                self.logger.error(f"解析box时出错: {e}, box值: {box}")
                return -1

        def detect_balls(image) -> list:
            """统一处理信号球识别"""
            ball_status: list = [None] * 8
            for color in ["red", "blue", "yellow"]:
                result = self.context.run_recognition(
                    "识别信号球", image, self.template.get(color, {})
                )
                self.logger.info(
                    f"识别到{color}球: {result.filterd_results if result else '无'}"
                )
                if result:
                    for item in result.filterd_results:
                        try:
                            pos = analyze_position(item.box)
                            # 确保pos是整数且在有效范围内
                            if isinstance(pos, int) and 0 <= pos < len(ball_status):
                                ball_status[pos] = color
                            else:
                                self.logger.warning(f"无效的位置索引: {pos}")
                        except Exception as e:
                            self.logger.error(f"处理信号球时出错: {e}")
            self.logger.info(f"信号球状态: {ball_status}")
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

            self.logger.info(f"有效长度: {valid_length}")

            if valid_length == 0:
                self.logger.info("未找到有效操作")
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
                    self.logger.info(
                        f"第一优先级：{'任意' if is_any else '目标'}三连消除"
                    )
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
                            self.logger.info(
                                f"第二优先级：可形成{'任意' if is_any else '目标'}三连"
                            )
                            return -(i + 1)

                    if (is_any and temp[j] == temp[j + 1]) or (
                        not is_any and temp[j] == target and temp[j + 1] == target
                    ):
                        self.logger.info(
                            f"第二优先级：可形成{'任意' if is_any else '目标'}二连"
                        )
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
                        self.logger.info("第三优先级：任意三连消除")
                        return -(i + 1)
            return 0

        def _select_non_empty(ball_list: list) -> int:
            """选择非空元素"""
            return -2 if ball_list[0] is None else -1

        # 主逻辑流程
        try:
            image = self.context.tasker.controller.post_screencap().wait().get()
            ball_list = detect_balls(image)
            target = _find_optimal_ball(ball_list, target_ball)
            self.logger.info(f"最终目标球: {target}")
            return target
        except Exception as e:
            self.logger.info(f"消球决策异常: {str(e)}")
            return 0
