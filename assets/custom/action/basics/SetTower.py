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
MAA_Punish 放置计算器
作者:overflow65537
"""

from maa.context import Context
from maa.custom_action import CustomAction


class SetTower(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        image = context.tasker.controller.post_screencap().wait().get()
        target_pos = context.run_recognition("战斗地块_寒境曙光", image)
        if target_pos:
            image = context.tasker.controller.post_screencap().wait().get()
            empty_pos = context.run_recognition(
                "识别周围空地",
                image,
                {
                    "识别周围空地": {
                        "roi": "战斗地块_寒境曙光",
                        "roi_offset": [-240, -180, 380, 320],
                    }
                },
            )
            if empty_pos:
                context.tasker.controller.post_click(
                    empty_pos.best_result.box[0], empty_pos.best_result.box[1]
                ).wait()
        return CustomAction.RunResult(success=True)
