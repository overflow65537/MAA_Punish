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
    def __init__(self):
        super().__init__()
        self.logger = Logger("RoleSelection")

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        #condition = json.loads(argv.custom_action_param)
        condition = {"need_element": "fire"}
        role = {}

        role_dict = ROLE_ACTIONS.copy()
        for _ in range(5):  # 最多尝试5次识别
            role.update(self.recognize_role(context, role_dict))
            context.run_task("滑动_选人")

        role_weight = self.calculate_weight(role, condition)
        self.logger.info(f"角色权重: {role_weight}")

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
            self.logger.info(f"使用模板: {role_actions['template']}")
            self.logger.info(f"当前pipeline_override: {pipeline_override}")

            result = context.run_recognition(
                entry="识别角色",
                image=image,
                pipeline_override=pipeline_override,
            )

            # 检查识别结果并提取box信息
            if result and isinstance(result.best_result, TemplateMatchResult):
                self.logger.info(f"识别到角色: {role_name}")
                role[role_name] = role_actions.copy()
                context.run_task("识别战斗参数")
                combat_score = context.run_recognition("识别战力", image)
                if combat_score and isinstance(combat_score.best_result, OCRResult):
                    role[role_name]["combat_score"] = combat_score.best_result.text
        return role

    # 计算权重
    def calculate_weight(self, role_info: dict, condition: dict) -> dict:
        """
        公式
        权重 = (战力 + ( 属性分数 * 60) + (代数分数 * 1000)) * 是否有次数
        """
        weight = []

        for role_name, info in role_info.items():
            #战力
            combat_score = info.get("combat_score", 0)
            if isinstance(combat_score, str) and combat_score.isdigit():
                combat_score = int(combat_score)
            elif isinstance(combat_score, int):
                pass
            else:
                combat_score = 0
            #属性分数
            attribute_score = info.get(condition.get("need_element", ""), 0)
            #代数分数
            element_score = info.get("generation", 0)
            #权重
            w = (combat_score + (attribute_score * 30) + (element_score * 1000))    
            weight.append((role_name, w))
        return dict(weight)