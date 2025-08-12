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
MAA_Punish 打印识别信息
作者:overflow65537
"""

from maa.context import Context
from maa.custom_action import CustomAction
from maa.define import OCRResult

from assets.custom import action


class PrintInfo(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        if isinstance(argv.reco_detail.best_result, OCRResult):
            if argv.reco_detail.best_result.text:
                context.override_pipeline(
                    {
                        "自定义信息_为了防止重复所以名字长一点": {
                            "focus": {
                                "succeeded": f"[color:Tomato]当前识别结果:{argv.reco_detail.best_result.text}[/color]",
                            }
                        }
                    }
                )
            else:
                context.override_pipeline(
                    {
                        "自定义信息_为了防止重复所以名字长一点": {
                            "focus": {
                                "succeeded": f"[color:Tomato]未识别到任何信息,已保存截图至debug目录[/color]",
                            },
                            "action": {
                                "type": "Custom",
                                "param": {
                                    "custom_action": "ScreenShot",
                                    "custom_action_param": {"type": "OC"},
                                },
                            },
                        }
                    }
                )

        else:
            context.override_pipeline(
                {
                    "自定义信息_为了防止重复所以名字长一点": {
                        "focus": {
                            "succeeded": f"[color:Tomato]当前识别结果:{argv.reco_detail.best_result}[/color]",
                        }
                    }
                }
            )
        context.run_task("自定义信息_为了防止重复所以名字长一点")
        return CustomAction.RunResult(success=True)
