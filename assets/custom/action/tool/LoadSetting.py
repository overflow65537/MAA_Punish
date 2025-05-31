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
MAA_Punish 角色配置载入
作者:HCX0426
"""

import json
import os
import sys
from pathlib import Path

# 获取当前文件的绝对路径
current_file = Path(__file__).resolve()

# 定义可能的项目根目录相对路径
root_paths = [
    current_file.parent.parent.parent.parent.joinpath("MFW_resource"),
    current_file.parent.parent.parent.parent.parent.parent.joinpath("Bundles").joinpath(
        "MAA_Punish"
    ),
    current_file.parent.parent.parent.parent.parent.joinpath("assets"),
]

# 确定项目根目录
project_root = next((path for path in root_paths if path.exists()), None)
if project_root:
    if project_root == current_file.parent.parent.parent.parent.joinpath(
        "MFW_resource"
    ):
        project_root = current_file.parent.parent.parent.parent
    print(f"项目根目录: {project_root}")

    # 添加项目根目录到sys.path
    sys.path.append(str(project_root))


class LoadSetting:
    def __init__(self):
        self._role_actions = self.load_role_setting()

    @property
    def role_actions(self):
        return self._role_actions

    @staticmethod
    def load_role_setting():
        try:
            with open(
                os.path.join(os.path.dirname(__file__), "..", "setting.json"),
                "r",
                encoding="utf-8",
            ) as file:
                return json.load(file).get("ROLE_ACTIONS", {})
        except FileNotFoundError:
            with open("setting.json", "r", encoding="utf-8") as file:
                return json.load(file).get("ROLE_ACTIONS", {})
        except json.JSONDecodeError:
            print("setting.json 文件格式错误。")
            return {}


# 角色名称到动作的映射表
ROLE_ACTIONS = LoadSetting.load_role_setting()
