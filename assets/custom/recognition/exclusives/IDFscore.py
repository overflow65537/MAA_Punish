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
MAA_Punish 肉鸽4分数识别
作者:overflow65537
"""

from maa.context import Context
from maa.custom_recognition import CustomRecognition


class IDFscore(CustomRecognition):

    def analyze(
        self,
        context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        image = context.tasker.controller.post_screencap().wait().get()
        # 检查目标分数
        context.run_recognition("检查目标分数区域", image)
        target_score = context.run_recognition("检查目标分数", image)
        # 检查当前分数
        context.run_recognition("检查当前分数区域", image)
        current_score = context.run_recognition("检查当前分数", image)
        if current_score is None or target_score is None:
            return
        if (
            current_score.best_result.text.isdigit()
            and target_score.best_result.text.isdigit()
        ):

            if int(current_score.best_result.text) >= int(
                target_score.best_result.text
            ):
                return CustomRecognition.AnalyzeResult(
                    box=(0, 0, 100, 100),
                    detail=f"{current_score.best_result.text}>={target_score.best_result.text}",
                )
        else:
            return
