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
from maa.define import ColorMatchResult, TemplateMatchResult
import time
import re
from MPAcustom.action.tool.LoadSetting import ROLE_ACTIONS
from MPAcustom.logger_component import LoggerComponent


class CombatActions:
    """通用战斗功能"""

    def __init__(self, context: Context, role_name: str = ""):
        self.context = context
        self.role_name = role_name

        self.template = {}
        if role_name in ROLE_ACTIONS:
            self.template = ROLE_ACTIONS[role_name].get("skill_template", {})
        else:
            for role in ROLE_ACTIONS.values():
                if role_name == role["name"]:
                    self.template = role.get("skill_template", {})
                    break
        self._logger_component = LoggerComponent(__name__)
        self.logger = self._logger_component.logger
        auto_qte_config = self.context.get_node_data("自动qte") or {}
        switch_config = self.context.get_node_data("自动切换") or {}
        self.auto_qte_config = auto_qte_config.get("enabled", False)
        self.switch_config = switch_config.get("enabled", False)

    def attack(self):
        """
        攻击
        执行一次攻击操作。
        """
        image = self.context.tasker.controller.post_screencap().wait().get()
        result = self.context.run_recognition("战斗中", image)
        if result and result.hit:
            return self.context.run_action("攻击")
        else:
            return False

    def continuous_attack(self, count: int = 10, interval: int = 100) -> bool:
        """
        连续攻击
        连续执行多次攻击操作。
        :param count: 攻击次数，默认10
        :param interval: 每次攻击间隔（毫秒），默认100
        :return: True
        """
        for _ in range(count):
            start_time = time.monotonic()
            self.attack()
            elapsed_ms = (time.monotonic() - start_time) * 1000
            remaining_ms = interval - elapsed_ms
            if remaining_ms > 0:
                time.sleep(remaining_ms / 1000)
        return True

    def long_press_attack(self, duration: int = 1000):
        """
        长按攻击
        按住攻击键一段时间。
        :param duration: 长按时间（毫秒），默认1000
        """
        if duration != 1000:
            self.context.override_pipeline(
                {"长按攻击": {"action": {"param": {"duration": duration}}}}
            )
        return self.context.run_action("长按攻击")

    def dodge(self):
        """
        闪避
        执行一次闪避操作。
        """
        return self.context.run_action("闪避")

    def long_press_dodge(self, duration: int = 1000):
        """
        长按闪避
        按住闪避键一段时间。
        :param duration: 长按时间（毫秒），默认1000
        """
        if duration != 1000:
            self.context.override_pipeline(
                {"长按闪避": {"action": {"param": {"duration": duration}}}}
            )
        return self.context.run_action("长按闪避")

    def use_skill(self, duration: int = 0):
        """
        使用技能
        执行一次技能释放操作。
        :param duration: 技能释放后等待时间（毫秒），默认0
        """

        self.context.run_action("技能")
        time.sleep(duration / 1000)
        return True

    def long_press_skill(self, time: int = 1000):
        """
        长按技能
        按住技能键一段时间。
        :param time: 长按时间（毫秒），默认1000
        """
        if time != 1000:
            self.context.override_pipeline(
                {"长按技能": {"action": {"param": {"duration": time}}}}
            )
        return self.context.run_action("长按技能")

    def down_dodge(self, contact: int = 0):
        """
        按下闪避
        按下闪避操作。
        :param contact: 触摸编号
        """
        self.context.override_pipeline(
            {"按下闪避": {"action": {"param": {"contact": contact}}}}
        )
        return self.context.run_action("按下闪避")

    def up_dodge(self, contact: int = 0):
        """
        松开闪避
        松开闪避操作。
        :param contact: 触摸编号
        """
        self.context.override_pipeline(
            {"松开闪避": {"action": {"param": {"contact": contact}}}}
        )
        return self.context.run_action("松开闪避")

    def ball_elimination_target(self, target: int = 2):
        """
        指定消球位置
        消除指定位置的信号球。
        :param target: 消球位置（1~8），默认2
        """
        target = abs(target)
        if target == 0:
            target = 2
        elif target < 1 or target > 8:
            return False
        return self.context.run_action(f"消球{target}")

    def trigger_qte(self, target: int = 1):
        """
        触发QTE/换人
        执行QTE或换人操作。
        :param target: QTE位置（1或2），默认1
        :return: 点击操作结果
        """
        if target not in (1, 2):
            raise ValueError("target 参数必须为 1 或 2")
        return self.context.run_action(f"qte{target}")

    def _try_qte_by_color(self, color: str):
        """
        尝试触发指定颜色的QTE
        :param color: QTE颜色(r,y,b)
        :return: 成功返回点击操作结果，失败返回False
        """
        image = self.context.tasker.controller.post_screencap().wait().get()
        # 颜色映射字典
        color_map = {
            "r": "检查红色QTE待激发",
            "y": "检查黄色QTE待激发",
            "b": "检查蓝色QTE待激发",
        }

        if color not in color_map:
            return False

        qte_name = color_map[color]

        # 检查目标QTE是否存在
        target_color_reco = self.context.run_recognition(qte_name, image)
        if (
            target_color_reco
            and target_color_reco.hit
            and isinstance(target_color_reco.best_result, ColorMatchResult)
        ):
            print(target_color_reco.best_result)
            return self.context.tasker.controller.post_click(
                target_color_reco.best_result.box[0],
                target_color_reco.best_result.box[1],
            ).wait()
        return False

    def auto_qte(self, target: str = "a"):
        """
        触发QTE
        :param target: QTE颜色(r,y,b,a)，默认r。a表示依次检查r、b、y
        :return: 点击操作结果
        """
        if not self.auto_qte_config:
            self.logger.info("未开启自动QTE功能")
            return False

        # 处理自动模式：依次检查r、b、y
        if target == "a":
            for color in ["r", "b", "y"]:
                self._try_qte_by_color(color)
                time.sleep(0.05)
            return False

        # 处理单色模式
        result = self._try_qte_by_color(target)
        if result is False and target not in ("r", "y", "b"):
            raise ValueError("target 参数必须为 r, y, b, a")
        return result

    def lens_lock(self):
        """
        镜头锁定
        执行镜头锁定操作。
        """
        return self.context.run_action("锁定视角")

    def auxiliary_machine(self):
        """
        辅助机
        执行辅助机操作。
        """
        return self.context.run_action("辅助机")

    def check_status(self, node: str, pipeline_override: dict = {}):
        """
        检查状态
        检查指定Pipeline节点状态，返回识别结果。
        :param node: Pipeline节点名
        :param pipeline_override: 节点覆盖参数
        :return: 识别结果或False
        """
        try:
            # 获取截图
            image = self.context.tasker.controller.post_screencap().wait().get()
            # 识别并返回结果
            result = self.context.run_recognition(node, image, pipeline_override)
            if result and result.hit:
                return result
            else:
                return False
        except Exception as e:
            self.logger.exception(node + ":" + str(e))
            return False

    def check_Skill_energy_bar(self) -> bool:
        """
        检查技能能量条
        检查技能能量是否足够，足够时返回True。
        :return: bool
        """
        try:
            # 获取截图
            image = self.context.tasker.controller.post_screencap().wait().get()
            # 识别并返回结果
            energy_result = self.context.run_recognition("技能_能量条", image)
            return bool(energy_result and energy_result.hit)

        except Exception as e:
            self.logger.exception("检查技能_能量条:" + str(e))
            return False

    def Arrange_Signal_Balls(self, target_ball: str = "any") -> int:
        """
        识别三消位置
        自动消球逻辑，返回消球目标位置。耗时大约300ms
        :param target_ball: 目标球颜色（red|blue|yellow|any）
        :return: int，正数为三消目标，负数为可促成三消，0为无效
        """
        if self.template == {}:
            self.logger.error("模板未加载")
            return 0

        # 信号球位置坐标（用于位置分析）
        ball_positions = [
            (1220, 500),  # 1
            (1111, 500),  # 2
            (1003, 500),  # 3
            (894, 500),  # 4
            (786, 500),  # 5
            (677, 500),  # 6
            (569, 500),  # 7
            (460, 500),  # 8
        ]

        def analyze_position(box) -> int:
            """分析信号球位置"""
            try:
                # 确保box可以解包为4个整数
                x, y, w, h = box
                for idx, (pos_x, pos_y) in enumerate(ball_positions):
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
                has_hit = bool(result and result.hit)
                if result is None:
                    return []
                self.logger.info(
                    f"识别到{color}球: {result.filtered_results if has_hit else '无'}"
                )
                if has_hit:
                    for item in result.filtered_results:
                        if not isinstance(item, TemplateMatchResult):
                            continue
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
                            return -i

                    if (is_any and temp[j] == temp[j + 1]) or (
                        not is_any and temp[j] == target and temp[j + 1] == target
                    ):
                        self.logger.info(
                            f"第二优先级：可形成{'任意' if is_any else '目标'}二连"
                        )
                        candidate = -i
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
                        return -i
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

    def count_signal_balls(self) -> int:
        """
        统计当前信号球数量
        识别当前场景信号球数量。
        :return: int，信号球数量
        """
        image = self.context.tasker.controller.post_screencap().wait().get()
        result = self.context.run_recognition("统计信号球数量", image)
        from maa.define import OCRResult

        if result and result.hit and isinstance(result.best_result, OCRResult):
            num = re.search(r"\d+", result.best_result.text)
            if num:
                self.logger.info(f"识别到信号球数量: {int(num.group())}")
                return int(num.group())

        return 0

    def get_hp_percent(self) -> int:
        """
        获取当前血量百分比
        识别当前角色血量百分比。
        :return: int，血量百分比（0~100）
        """
        image = self.context.tasker.controller.post_screencap().wait().get()
        result = self.context.run_recognition("检查血量百分比", image)

        if result and result.hit and isinstance(result.best_result, ColorMatchResult):
            hp_pixels = int(result.best_result.count)
            hp_percent = int((hp_pixels / 429) * 100)
            self.logger.info(f"当前血量百分比: {hp_percent}%")
            return min(max(hp_percent, 0), 100)
        else:
            return 0

    def Switch(self):
        """
        切换角色
        """
        if not self.switch_config:
            self.logger.info("未开启切换角色功能")
            return
        role_type = ROLE_ACTIONS.get(self.role_name, {}).get("type", "general")
        print(f"当前角色: {role_type}")

        def _click_qte(color: str):
            mapping = {
                "blue": "切换蓝色QTE",
                "yellow": "切换黄色QTE",
                "red": "切换红色QTE",
            }
            reco_name = mapping.get(color, "")
            image = self.context.tasker.controller.cached_image
            qte = self.context.run_recognition(reco_name, image)
            if qte and qte.hit:
                print(f"找到{color}QTE")
                self.context.tasker.controller.post_click(
                    qte.best_result.box[0], qte.best_result.box[1]  # type: ignore
                )

                for _ in range(100):
                    image = self.context.tasker.controller.post_screencap().wait().get()
                    qte = self.context.run_recognition(reco_name, image)
                    self.attack()
                    if qte and qte.hit:
                        self.context.tasker.controller.post_click(
                            qte.best_result.box[0], qte.best_result.box[1]  # type: ignore
                        )
                    else:
                        break

            else:
                print(f"未找到{color}QTE")
                print(qte)

        def _create_qte_mapping():
            image = self.context.tasker.controller.post_screencap().wait().get()
            candidates = []
            for color, reco_name in (
                ("blue", "切换蓝色QTE"),
                ("yellow", "切换黄色QTE"),
                ("red", "切换红色QTE"),
            ):
                result = self.context.run_recognition(reco_name, image)
                if result and result.hit and result.best_result:
                    box = result.best_result.box  # type: ignore[attr-defined]
                    # box 为 xywh，按中心 y 值排序
                    center_y = box[1] + box[3] / 2
                    candidates.append((center_y, color))

            candidates.sort(key=lambda item: item[0])
            # 返回颜色列表：0 为最上面，1 为最下面
            return [color for _, color in candidates]

        localtion_mapping = _create_qte_mapping()

        target_node = self.context.get_node_data("QTE目标")
        if not target_node:
            self.logger.error("未找到QTE目标 node")
            return
        target = int(target_node.get("post_delay", 0))
        if target == 0:
            _click_qte(localtion_mapping[1])
            self.context.override_pipeline({"QTE目标": {"post_delay": 0}})
        elif target == 1:
            _click_qte(localtion_mapping[0])
            self.context.override_pipeline({"QTE目标": {"post_delay": 1}})
        else:
            return

        self.context.override_pipeline({"识别人物": {"enabled": True}})
