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
MAA_Punish 重置特殊识别
作者:overflow65537
"""

from maa.context import Context
from maa.custom_action import CustomAction
import json


class ResetIdentify(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        argv: dict = json.loads(argv.custom_action_param)
        print(f"argv: {argv}")
        if not argv:
            context.override_pipeline({"识别人物": {"enabled": True}})

        elif argv.get("mode") == "矩阵循生":

            context.override_pipeline(
                {
                    "选择首发_矩阵循生": {"enabled": False},
                    "异度投影_矩阵循生": {"enabled": False},
                    "进入物归新主_矩阵循生": {"enabled": True},
                    "选择首发2_矩阵循生": {"enabled": True},
                    "矩阵循生": {
                        "action": "custom",
                        "custom_action": "ResetIdentify",
                        "custom_action_param": {"mode": "矩阵循生"},
                    },
                }
            )

        return CustomAction.RunResult(success=True)
