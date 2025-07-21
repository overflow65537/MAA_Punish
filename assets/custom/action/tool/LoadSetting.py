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

current_file = Path(__file__).resolve()
sys.path.append(str(current_file.parent.parent.parent.parent))

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
