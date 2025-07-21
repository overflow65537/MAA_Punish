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
MAA_Punish 识别角色
作者:HCX0426
"""

import sys
import time
from pathlib import Path
from typing import Dict, Optional

from maa.context import Context
from maa.custom_action import CustomAction
from xtyping import F

# 获取当前文件的绝对路径
current_file = Path(__file__).resolve()
sys.path.append(str(current_file.parent.parent.parent.parent))
from custom.action.tool.LoadSetting import ROLE_ACTIONS

class IdentifyRoles(CustomAction):
    def run(self, context: Context, _: CustomAction.RunArg) -> CustomAction.RunResult:

        # ROI区域配置（x, y, w, h）
        ROLE_NAME_ROIS = [
            ("pos1", (209, 303, 259, 46)),
            ("pos2", (514, 308, 252, 43)),
            ("pos3", (821, 302, 243, 51)),
        ]

        LEADER_FLAG_ROIS = [
            ("pos1", (236, 509, 210, 59)),
            ("pos2", (535, 512, 212, 53)),
            ("pos3", (850, 509, 183, 61)),
        ]

        # 进入角色选择界面
        context.run_task("点击更换")
        time.sleep(1)

        # 获取屏幕截图
        image = context.tasker.controller.post_screencap().wait().get()

        # 识别角色名称
        role_names: Dict[str, Optional[str]] = {}
        for pos, roi in ROLE_NAME_ROIS:
            result = context.run_recognition(
                "识别角色名", image, {"识别角色名": {"roi": roi}}
            )
            role_names[pos] = result.best_result.text if result else None

        # 识别队长标志
        leader_flags: Dict[str, bool] = {}
        for pos, roi in LEADER_FLAG_ROIS:
            result = context.run_recognition(
                "识别队长位置", image, {"识别队长位置": {"roi": roi}}
            )
            leader_flags[pos] = bool(result.best_result.text) if result else False

        print("识别结果:", role_names)
        print("队长标记:", leader_flags)
        if (
            not leader_flags.get("pos1")
            and not leader_flags.get("pos2")
            and not leader_flags.get("pos3")
        ):  # 未找到队长,通常是只有一个角色在1号位,但队长标记在2号位
            context.run_task("选择队长")  # 随便选择一个队长
        # 退出角色选择界面
        context.run_task("出队长界面")

        # 匹配角色并获取对应动作
        matched_roles = {
            pos: ROLE_ACTIONS[name]
            for pos, name in role_names.items()
            if name in ROLE_ACTIONS
        }

        # 处理匹配结果
        match len(matched_roles):
            case 1:  # 单个角色匹配
                pos, action = next(iter(matched_roles.items()))

                # 设置队长位置(单个角色特用)
                if leader_flags.get(pos):
                    color_map = {"pos1": "蓝色", "pos2": "红色", "pos3": "黄色"}
                    context.run_task(
                        "点击首选位置", {"点击首选位置": {"expected": color_map[pos]}}
                    )

                # 覆写战斗流程
                context.override_pipeline(
                    {
                        "角色特有战斗": {"action": "Custom", "custom_action": action},
                        "自动战斗开始": {"next": ["单人自动战斗循环"]},
                    }
                )
            case n if n > 1:  # 多个角色匹配
                context.override_pipeline(
                    {
                        "自动战斗开始": {"next": ["多人轮切自动战斗循环"]},
                    }
                )
            case _:  # 无匹配角色
                if len(role_names) == 1:
                    # 设置队长位置(单个角色特用)
                    if leader_flags.get(pos):
                        color_map = {"pos1": "蓝色", "pos2": "红色", "pos3": "黄色"}
                        context.run_task(
                            "点击首选位置",
                            {"点击首选位置": {"expected": color_map[pos]}},
                        )

                context.override_pipeline(
                    {
                        "自动战斗开始": {"next": ["通用自动战斗循环"]},
                    }
                )

        context.run_task("点击作战开始")
        return CustomAction.RunResult(success=True)
