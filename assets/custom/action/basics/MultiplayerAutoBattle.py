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
MAA_Punish 多人自动战斗
作者:HCX0426
"""

import sys
from pathlib import Path

from maa.context import Context
from maa.custom_action import CustomAction

# 获取当前文件的绝对路径
current_file = Path(__file__).resolve()
sys.path.append(str(current_file.parent.parent.parent.parent))
from custom.action.tool.LoadSetting import ROLE_ACTIONS


class MultiplayerAutoBattle(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        try:
            image = context.tasker.controller.post_screencap().wait().get()

            # 检查当前角色
            recognized_role = None
            for role_name, action in ROLE_ACTIONS.items():
                result = context.run_recognition(f"检查{role_name}", image)
                if result is not None:
                    recognized_role = {"action": "Custom", "custom_action": action}
                    break

            if recognized_role:
                context.override_pipeline({"角色特有战斗": recognized_role})
                max_battles = 8
            else:
                context.override_pipeline({"通用战斗模式": {}})
                max_battles = 3

            n = 0
            while n < max_battles:
                context.run_task("角色特有战斗" if recognized_role else "通用战斗模式")
                n += 1

            return CustomAction.RunResult(success=True)
        except Exception as e:
            # 捕获异常并记录错误信息
            print(f"执行MultiplayerAutoBattle时发生错误: {e}")
            return CustomAction.RunResult(success=False)
