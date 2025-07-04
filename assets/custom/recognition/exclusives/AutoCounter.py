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
MAA_Punish 自动战斗反击程序
作者:overflow65537
"""

from maa.custom_recognition import CustomRecognition
import json

class AutoCounter(CustomRecognition):


    def analyze(
        self,
        context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        image = context.tasker.controller.post_screencap().wait().get()
        #是否在战斗状态
        in_battle = context.run_recognition(
            "战斗中", image,
        )
        if not in_battle:
            return 
        #当前血量
        current_hp = json.loads(argv.custom_recognition_param).get("current_hp", None)

        #检测血量
        expected_hp = context.run_recognition(
            "检查血量", image,
        )
        if not expected_hp:
            return 
        if current_hp is None or expected_hp.best_result.text !=current_hp:
            context.override_pipeline(
                {
                    argv.node_name: {
                        "custom_recognition_param": {
                            "current_hp": expected_hp.best_result.text
                        }
                    }
                },
            )

            return CustomRecognition.AnalyzeResult(
                    box=(1193,637, 100, 100), detail="success"
                )
        return