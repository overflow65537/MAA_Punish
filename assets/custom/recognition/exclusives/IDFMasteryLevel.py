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
MAA_Punish 特殊识别器,识别精通等级
作者:overflow65537
"""

from maa.context import Context
from maa.custom_recognition import CustomRecognition


class IDFMasteryLevel(CustomRecognition):

    def analyze(
        self,
        context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        result = context.run_recognition(
            "选择自动作战人物_矩阵循生",
            argv.image,
            {
                "选择自动作战人物_矩阵循生": {
                    "template": [
                        "肉鸽通用/誓焰终解_矩阵.png",
                        "肉鸽通用/誓焰_矩阵.png",
                        "肉鸽通用/誓焰花嫁_矩阵.png",
                        "肉鸽通用/深红囚影终解_矩阵.png",
                        "肉鸽通用/深红囚影_矩阵.png",
                        "肉鸽通用/深谣终解_矩阵.png",
                        "肉鸽通用/深谣_矩阵.png",
                        "肉鸽通用/终焉终解_矩阵.png",
                        "肉鸽通用/终焉_矩阵.png",
                        "肉鸽通用/深痕终解_矩阵.png",
                        "肉鸽通用/深痕_矩阵.png",
                    ],
                    "threshold": [
                        0.9,
                        0.9,
                        0.9,
                        0.9,
                        0.9,
                        0.9,
                        0.9,
                        0.9,
                        0.9,
                        0.9,
                        0.9,
                    ],
                }
            },
        )
        if result:
            for i in result.filterd_results:
                if context.run_recognition(
                    "识别精通等级",
                    argv.image,
                    {
                        "识别精通等级": {
                            "roi": i.box,
                            "roi_offset": [189, 25, -51, -45],
                        }
                    },
                ):
                    context.override_pipeline(
                        {
                            "战斗事件_矩阵循生": {
                                "interrupt": [
                                    "识别人物",
                                    "重启_寒境曙光",
                                    "战斗中",
                                    "出击_矩阵循生",
                                    "跳过战斗对话",
                                    "进入战斗_矩阵循生",
                                    "载入中",
                                ]
                            },
                            "识别人物": {"enabled": True},
                        }
                    )
                    print("IDFMasteryLevel success")
                    return CustomRecognition.AnalyzeResult(box=i.box, detail="success")
        print("IDFMasteryLevel failed")
        return
