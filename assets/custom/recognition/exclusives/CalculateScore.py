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
MAA_Punish 肉鸽4分数计算
作者:overflow65537
"""

from maa.context import Context
from maa.custom_recognition import CustomRecognition


class CalculateScore(CustomRecognition):

    def analyze(
        self,
        context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        image = context.tasker.controller.post_screencap().wait().get()
        # 检查目标分数
        target_score = context.run_recognition("检查目标分数", image)
        # 检查当前分数
        current_score = context.run_recognition("检查当前分数", image)

        # 检查军事分数及倍率
        military_score = context.run_recognition(
            "检查分数", image, {"检查分数": {"roi": [90, 238, 105, 44]}}
        )
        military_multiplier = context.run_recognition(
            "检查分数", image, {"检查分数": {"roi": [197, 239, 54, 48], "expected": ""}}
        )

        # 检查经济分数及倍率
        economic_score = context.run_recognition(
            "检查分数", image, {"检查分数": {"roi": [90, 327, 105, 44]}}
        )
        economic_multiplier = context.run_recognition(
            "检查分数", image, {"检查分数": {"roi": [193, 323, 61, 52], "expected": ""}}
        )

        # 检查科研分数及倍率
        research_score = context.run_recognition(
            "检查分数", image, {"检查分数": {"roi": [90, 412, 107, 46]}}
        )
        research_multiplier = context.run_recognition(
            "检查分数", image, {"检查分数": {"roi": [196, 416, 61, 43], "expected": ""}}
        )

        if None in [
            current_score,
            target_score,
            military_score,
            military_multiplier,
            economic_score,
            economic_multiplier,
            research_score,
            research_multiplier,
        ]:
            return

        if (
            current_score.best_result.text.isdigit()
            and target_score.best_result.text.isdigit()
            and military_score.best_result.text.isdigit()
            and military_multiplier.best_result.text[1:].isdigit()
            and economic_score.best_result.text.isdigit()
            and economic_multiplier.best_result.text[1:].isdigit()
            and research_score.best_result.text.isdigit()
            and research_multiplier.best_result.text[1:].isdigit()
        ):
            final_score = (
                int(military_score.best_result.text)
                * int(military_multiplier.best_result.text[1:])
                + int(economic_score.best_result.text)
                * int(economic_multiplier.best_result.text[1:])
                + int(research_score.best_result.text)
                * int(research_multiplier.best_result.text[1:])
                + int(current_score.best_result.text)
            )
            print(final_score)
            if final_score >= int(target_score.best_result.text):
                return CustomRecognition.AnalyzeResult(
                    box=(0, 0, 100, 100), detail="success"
                )
        else:
            return
