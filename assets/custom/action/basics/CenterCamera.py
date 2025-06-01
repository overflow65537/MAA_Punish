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
MAA_Punish 肉鸽4重置镜头
作者:overflow65537
"""


from maa.context import Context
from maa.custom_action import CustomAction
import time


class CenterCamera(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        image = context.tasker.controller.post_screencap().wait().get()
        if argv.custom_action_param == '{"tower":true}':
            origin_pos = context.run_recognition("战斗地块_寒境曙光", image)
            if not origin_pos or not origin_pos.best_result:
                return CustomAction.RunResult(success=True)
            x, y = (
                origin_pos.best_result.box[0],
                origin_pos.best_result.box[1],
            )
            context.tasker.controller.post_swipe(x, y, 764, 334, 2000).wait()
            time.sleep(1)
            context.tasker.controller.post_click(100, 100).wait()
            time.sleep(1)
            return CustomAction.RunResult(success=True)
        else:
            origin_pos = context.run_recognition("重置镜头", image)
            if not origin_pos or not origin_pos.best_result:
                return CustomAction.RunResult(success=True)
            x, y = (
                origin_pos.best_result.box[0],
                origin_pos.best_result.box[1],
            )
            context.tasker.controller.post_swipe(x, y, 1052, 342, 2000).wait()
            time.sleep(1)
            context.tasker.controller.post_click(100, 100).wait()
            time.sleep(1)
            return CustomAction.RunResult(success=True)
