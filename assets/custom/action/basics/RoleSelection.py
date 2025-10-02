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
MAA_Punish 选择角色
作者:overflow65537
"""

from email.mime import image
from maa.context import Context
from maa.custom_action import CustomAction
from maa.define import TemplateMatchResult, OCRResult
import sys
from pathlib import Path
import json


# 获取当前文件的绝对路径
current_file = Path(__file__).resolve()
sys.path.append(str(current_file.parent.parent.parent.parent))
from custom.action.tool.LoadSetting import ROLE_ACTIONS
from custom.action.tool.logger import Logger


class RoleSelection(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        self.logger = Logger("RoleSelection").get_logger()
        condition = json.loads(argv.custom_action_param)
        if condition is None:
            condition = {}
        role = {}

        role_dict = ROLE_ACTIONS.copy()
        for _ in range(int(condition.get("max_try", 3))):
            if context.tasker.stopping:
                return CustomAction.RunResult(success=True)
            role.update(self.recognize_role(context, role_dict))
            context.run_action("滑动_选人")

        role_weight = self.calculate_weight(role, condition)
        self.logger.info(f"条件: {condition}")
        self.logger.info(f"角色权重: {role_weight}")
        # 找出权重最高的key
        selected_role = max(role_weight, key=lambda x: x[1])[0]

        self.logger.info(f"选择角色: {selected_role}")
        for _ in range(int(condition.get("max_try", 3))):
            if context.tasker.stopping:
                return CustomAction.RunResult(success=True)
            context.run_action("反向滑动_选人")
        target = None
        for _ in range(int(condition.get("max_try", 3)) + 1):
            if context.tasker.stopping:
                return CustomAction.RunResult(success=True)
            image = context.tasker.controller.post_screencap().wait().get()
            target = context.run_recognition(
                "选择人物",
                image,
                {
                    "选择人物": {
                        "recognition": {
                            "param": {"template": role_dict[selected_role]["template"]},
                        },
                    }
                },
            )
            if target and isinstance(target.best_result, TemplateMatchResult):
                context.tasker.controller.post_click(
                    target.best_result.box[0] + target.best_result.box[2] // 2,
                    target.best_result.box[1] + target.best_result.box[3] // 2,
                ).wait()
                context.run_task("编入队伍")
                self.logger.info(f"选择角色成功: {selected_role}")
                return CustomAction.RunResult(success=True)
            context.run_action("滑动_选人")
        if target is None:
            self.logger.info(f"选择角色失败: {selected_role}")
            context.run_task("返回主菜单")
            context.tasker.post_stop()

        return CustomAction.RunResult(success=True)

    def recognize_role(self, context: Context, role_actions: dict) -> dict:

        # 对每个角色进行识别
        role = {}
        image = context.tasker.controller.post_screencap().wait().get()
        for role_name, role_actions in role_actions.items():

            pipeline_override = {
                "识别角色": {
                    "recognition": {
                        "param": {"template": role_actions["template"]},
                    },
                }
            }
            self.logger.info(f"正在识别角色: {role_name}")

            result = context.run_recognition(
                entry="识别角色",
                image=image,
                pipeline_override=pipeline_override,
            )

            # 检查识别结果并提取box信息
            if result and isinstance(result.best_result, TemplateMatchResult):
                self.logger.info(f"识别到角色: {role_name}")
                role[role_name] = role_actions.copy().get("metadata", {})
        return role

    # 计算权重
    def calculate_weight(
        self, role_info: dict, condition: dict[str, dict]
    ) -> list[dict]:
        """
        公式
        权重 = (( 属性分数 * 45) + (代数分数 * 2300)) * 是否有次数
        """
        weight = []

        for role_name, info in role_info.items():
            # 属性分数
            attribute_score = info.get(condition.get("need_element", ""), 0)
            # 代数分数
            element_score = info.get("generation", 0)
            # 权重
            w = (attribute_score * 45) + (element_score * 2300)
            weight.append((role_name, w))
        return weight
