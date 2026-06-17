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

from MPAcustom.logger_component import LoggerComponent


class NextStageRecognition(CustomRecognition):
    def analyze(
        self,
        context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult | None:
        logger_component = LoggerComponent(__name__)
        logger = logger_component.logger
        image = argv.image
        logger.info("[NextStageRecognition] 开始识别下一关")
        # 当前章节
        current_stage_reco = context.run_recognition(
            "检查当前章节",
            image,
        )
        if not (
            current_stage_reco
            and current_stage_reco.hit
            and isinstance(current_stage_reco.best_result, OCRResult)
        ):
            logger.info("[NextStageRecognition] 检查当前章节未命中, 返回 None")
            return
        current_stage_text = current_stage_reco.best_result.text
        if "EX" in current_stage_text or "ER" in current_stage_text:
            current_stage = current_stage_text[:4]

        else:
            current_stage = current_stage_text[:2]
        if current_stage[0] == "0":
            current_stage = current_stage[1]
        logger.info(
            f"[NextStageRecognition] 当前章节 OCR={current_stage_text!r}, "
            f"解析章节={current_stage!r}"
        )
        # 最后关卡
        expected_pattern = f"^{current_stage}[-一1]?\\s*\\d+$"
        logger.info(
            f"[NextStageRecognition] 检查最后关卡, expected={expected_pattern!r}"
        )
        last_stage_reco = context.run_recognition(
            "检查最后关卡",
            image,
            {
                "检查最后关卡": {
                    "recognition": {
                        "param": {
                            "expected": expected_pattern,
                        },
                    }
                }
            },
        )
        if not (
            last_stage_reco
            and last_stage_reco.hit
            and isinstance(last_stage_reco.best_result, OCRResult)
        ):
            logger.info("[NextStageRecognition] 检查最后关卡未命中, 返回 None")
            return
        click_box = (
            last_stage_reco.best_result.box[0]
            + last_stage_reco.best_result.box[2],
            last_stage_reco.best_result.box[1]
            + last_stage_reco.best_result.box[3]
            + 50,
            0,
            0,
        )
        logger.info(
            f"[NextStageRecognition] 命中最后关卡 {last_stage_reco.best_result.text!r}, "
            f"点击坐标={click_box}"
        )
        return CustomRecognition.AnalyzeResult(
            box=(click_box,),
            detail={"status":"success","message":f"hit {last_stage_reco.best_result.text}"},
        )
