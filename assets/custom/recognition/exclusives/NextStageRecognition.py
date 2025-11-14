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
MAA_Punish 下一关识别程序
作者:overflow65537
"""

from maa.custom_recognition import CustomRecognition
from maa.define import OCRResult
import numpy as np


class NextStageRecognition(CustomRecognition):
    def analyze(
        self,
        context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult | None:
        image = argv.image
        # 当前章节
        current_stage_reco = context.run_recognition(
            "检查当前章节",
            image,
        )
        if not current_stage_reco or not isinstance(
            current_stage_reco.best_result, OCRResult
        ):
            return
        current_stage_text = current_stage_reco.best_result.text
        if "EX" in current_stage_text or "ER" in current_stage_text:
            current_stage = current_stage_text[:4]

        else:
            current_stage = current_stage_text[:2]
        if current_stage[0] == "0":
            current_stage = current_stage[1]
        # 最后关卡

        last_stage_reco = context.run_recognition(
            "检查最后关卡",
            image,
            {
                "检查最后关卡": {
                    "recognition": {
                        "param": {
                            "expected": f"^{current_stage}[-一1]?\\s*\\d+$",
                        },
                    }
                }
            },
        )
        if not last_stage_reco or not isinstance(
            last_stage_reco.best_result, OCRResult
        ):
            return
        return CustomRecognition.AnalyzeResult(
            box=(
                (
                    last_stage_reco.best_result.box[0]
                    + last_stage_reco.best_result.box[2],
                    last_stage_reco.best_result.box[1]
                    + last_stage_reco.best_result.box[3]
                    + 50,
                    0,
                    0,
                )
            ),
            detail=f"hit {last_stage_reco.best_result.text}",
        )
