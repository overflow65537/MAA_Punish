# Copyright (c) 2024-2025 MAA_SnowBreak
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
MAA_Punish 寒境蓝色地块检查
作者:overflow65537
"""

from maa.context import Context
from maa.custom_recognition import CustomRecognition
from numpy import ndarray


class CheckBlueZone(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult | None:
        image: ndarray = argv.image

        # 检查所有蓝色地块
        res = context.run_recognition("寒境蓝色地块检查", image=image)
        if not (res and res.hit):
            return CustomRecognition.AnalyzeResult(box=None, detail={"status": "no blue zone"})

        # 2. 遍历识别到的结果（开启 connected: true 后，连通域结果存放在 filtered_results 中）
        results = getattr(res, "filtered_results", None)
        if results is None:
            results = [res.best_result] if res.best_result else []

        for item in results:
            # 获取当前结果的 box，使用 getattr 规避 Pylance 对部分类型的属性访问警告
            box = getattr(item, "box", None)
            if not box:
                continue

            # 将当前地块的 box 设为 ROI，检查该区域内是否包含出生点特征
            exclude_res = context.run_recognition(
                "确认不是出生点",
                image=image,
                pipeline_override={
                    "确认不是出生点": {
                        "recognition": {
                            "param": {
                                "roi": box
                            }
                        }
                    }
                }
            )

            # 如果未命中出生点特征，说明这是我们需要的蓝色地块，返回对应的 box
            if not (exclude_res and exclude_res.hit):
                return CustomRecognition.AnalyzeResult(box=box, detail={"status": "success"})

        return CustomRecognition.AnalyzeResult(box=None, detail={"status": "all blue zones are birth points"})
