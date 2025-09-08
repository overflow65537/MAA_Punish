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

import sys
from pathlib import Path

current_file = Path(__file__).resolve()
sys.path.append(str(current_file.parent.parent.parent.parent))

# 角色名称到动作的映射表
ROLE_ACTIONS = {
    "露娜·终焉": "Oblivion",
    "比安卡·深痕": "Stigmata",
    "拉弥亚·深谣": "LostLullaby",
    "露西亚·深红囚影": "CrimsonWeave",
    "露西亚·誓焰": "Pyroath",
    "曲·启明": "Shukra",
    "里·超刻": "Hyperreal",
    "比安卡·晖暮": "Crepuscule",
}
