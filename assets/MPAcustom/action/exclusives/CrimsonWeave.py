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
MAA_Punish 囚影战斗程序
作者:overflow65537,HCX0426
"""


import time

from MPAcustom.action.basics import CombatActions
from maa.context import Context
from maa.custom_action import CustomAction
from maa.define import OCRResult


class CrimsonWeave(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:

        # 检查无光值等于300或者大于474,证明需要登龙
        self.light_less_474 = {
            "检查无光值_囚影": {
                "recognition": {
                    "type": "OCR",
                    "param": {
                        "roi": [473, 598, 41, 27],
                        "expected": "^(300|[4-5][7-9][4-9]|[4-5][0-9]{2}|600)$",
                    },
                }
            }
        }
        # 检查二阶段无光值存在,证明处在二阶段
        self.light_less_any = {
            "检查无光值_囚影": {
                "recognition": {
                    "type": "OCR",
                    "param": {
                        "roi": [473, 598, 41, 27],
                        "expected": "^(0|[1-9][0-9]?|[1-5][0-9][0-9]|600)$",
                    },
                }
            }
        }

        action = CombatActions(context, role_name="露西亚·深红囚影")
        action.lens_lock()

        if action.get_hp_percent() >= 70:
            action.dodge()  # 闪避
            for _ in range(7):
                start_time = time.time()
                action.attack()  # 宿命的囚笼由我斩断
                light_less = action.check_status(
                    "检查无光值_囚影",
                    self.light_less_any,
                )
                if light_less and light_less.best_result.text.isdigit():  # type: ignore
                    light_less_value = int(light_less.best_result.text)  # type: ignore
                else:
                    light_less_value = -1

                if light_less_value == -1:  # 处于一阶段
                    if action.check_Skill_energy_bar():
                        # 崩落的束缚化为利刃
                        for _ in range(10):
                            action.use_skill()
                            action.ball_elimination_target(1)
                            time.sleep(0.2)
                        break
                elif (
                    light_less_value == 300 or light_less_value >= 474
                ):  # 无光值足够登龙
                    action.long_press_dodge(1500)
                    action.long_press_attack(2300)  # 登龙
                    if action.check_Skill_energy_bar():
                        for _ in range(10):
                            action.use_skill()  # 宿命的囚笼由我斩断
                            time.sleep(0.2)
                    for _ in range(10):
                        action.ball_elimination_target(1)
                        time.sleep(0.2)
                    break
                elapsed = time.time() - start_time
                if elapsed < 0.3:
                    time.sleep(0.3 - elapsed)

        else:
            dodge_x = action.COORDINATES.get("dodge", ())[0]
            dodge_y = action.COORDINATES.get("dodge", ())[-1]
            context.tasker.controller.post_touch_down(dodge_x, dodge_y)
            start_time = time.time()

            if not action.check_status(
                "检查无光值_囚影",
                self.light_less_any,
            ):  # 处于一阶段
                elapsed = time.time() - start_time
                if elapsed < 1.5:
                    time.sleep(1.5 - elapsed)
                context.tasker.controller.post_touch_up()
                if action.check_Skill_energy_bar():
                    # 崩落的束缚化为利刃
                    for _ in range(10):
                        action.use_skill()
                        action.ball_elimination_target(1)
                        time.sleep(0.2)

            else:
                elapsed = time.time() - start_time
                if elapsed < 1.5:
                    time.sleep(1.5 - elapsed)
                context.tasker.controller.post_touch_up()
                action.long_press_attack(2300)  # 登龙
                if action.check_Skill_energy_bar():
                    for _ in range(10):
                        action.use_skill()  # 宿命的囚笼由我斩断
                        time.sleep(0.2)
                for _ in range(10):
                    action.ball_elimination_target(1)
                    time.sleep(0.2)

        return CustomAction.RunResult(True)
