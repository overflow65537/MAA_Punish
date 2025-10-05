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
作者:HCX0426,overflow65537
"""

import sys
from pathlib import Path

current_file = Path(__file__).resolve()
sys.path.append(str(current_file.parent.parent.parent.parent))

# 角色名称到动作的映射表
ROLE_ACTIONS = {
    "里·超刻": {
        # 部分场景下会识别这个名字
        "name": "超刻",
        # 自动战斗的动作名
        "cls_name": "Hyperreal",
        "metadata": {  # 角色的属性
            "fire": 100,
            # 代数
            "generation": 2,
        },
        # 角色头像模板
        "template": [
            "肉鸽通用/超刻.png",
            "肉鸽通用/超刻终解.png",
            "肉鸽通用/超刻_矩阵.png",
            "肉鸽通用/超刻终解_矩阵.png",
        ],
        # 角色攻击按键模板,用来在战斗内识别角色
        "attack_template": "自定义战斗/超刻.png",
        # 角色技能模板,用来自动释放三消
        "skill_template": {
            "red": {"识别信号球": {"template": ["信号球/超刻_红.png"]}},
            "blue": {"识别信号球": {"template": ["信号球/超刻_蓝.png"]}},
            "yellow": {"识别信号球": {"template": ["信号球/超刻_黄.png"]}},
        },
    },
    "露娜·终焉": {
        "name": "终焉",
        "cls_name": "Oblivion",
        "metadata": {
            "nihil": 100,
            "generation": 3,
        },
        "template": [
            "肉鸽通用/终焉.png",
            "肉鸽通用/终焉终解.png",
            "肉鸽通用/终焉_矩阵.png",
            "肉鸽通用/终焉终解_矩阵.png",
        ],
        "attack_template": "自定义战斗/终焉.png",
    },
    "比安卡·深痕": {
        "name": "深痕",
        "cls_name": "Stigmata",
        "metadata": {
            "physical": 100,
            "generation": 2,
        },
        "template": [
            "肉鸽通用/深痕.png",
            "肉鸽通用/深痕终解.png",
            "肉鸽通用/深痕_矩阵.png",
            "肉鸽通用/深痕终解_矩阵.png",
        ],
        "attack_template": "自定义战斗/深痕.png",
    },
    "拉弥亚·深谣": {
        "name": "深谣",
        "cls_name": "LostLullaby",
        "metadata": {
            "dark": 100,
            "generation": 2,
        },
        "template": [
            "肉鸽通用/深谣.png",
            "肉鸽通用/深谣终解.png",
            "肉鸽通用/深谣_矩阵.png",
            "肉鸽通用/深谣终解_矩阵.png",
        ],
        "attack_template": "自定义战斗/深谣_p1..png",
    },
    "露西亚·深红囚影": {
        "name": "深红囚影",
        "cls_name": "CrimsonWeave",
        "metadata": {
            "lightning": 100,
            "generation": 2,
        },
        "template": [
            "肉鸽通用/深红囚影.png",
            "肉鸽通用/深红囚影终解.png",
            "肉鸽通用/深红囚影_矩阵.png",
            "肉鸽通用/深红囚影终解_矩阵.png",
        ],
        "attack_template": "自定义战斗/深红囚影.png",
    },
    "露西亚·誓焰": {
        "name": "誓焰",
        "cls_name": "Pyroath",
        "metadata": {
            "fire": 100,
            "generation": 3,
        },
        "template": [
            "肉鸽通用/誓焰.png",
            "肉鸽通用/誓焰终解.png",
            "肉鸽通用/誓焰花嫁_矩阵.png",
            "肉鸽通用/誓焰终解_矩阵.png",
            "肉鸽通用/誓焰_矩阵.png",
        ],
        "attack_template": "自定义战斗/誓焰.png",
    },
    "曲·启明": {
        "name": "启明",
        "cls_name": "Shukra",
        "metadata": {
            "ice": 100,
            "generation": 2,
        },
        "template": [
            "肉鸽通用/启明.png",
            "肉鸽通用/启明终解.png",
            "肉鸽通用/启明_矩阵.png",
            "肉鸽通用/启明终解_矩阵.png",
        ],
        "attack_template": "自定义战斗/启明.png",
        "skill_template": {
            "red": {"识别信号球": {"template": ["信号球/启明_红.png"]}},
            "blue": {"识别信号球": {"template": ["信号球/启明_蓝.png"]}},
            "yellow": {"识别信号球": {"template": ["信号球/启明_黄.png"]}},
        },
    },
    "比安卡·晖暮": {
        "name": "晖暮",
        "cls_name": "Crepuscule",
        "metadata": {
            "dark": 100,
            "generation": 2,
        },
        "template": [
            "肉鸽通用/晖暮.png",
            "肉鸽通用/晖暮终解.png",
            "肉鸽通用/晖暮_矩阵.png",
            "肉鸽通用/晖暮终解_矩阵.png",
        ],
        "attack_template": "自定义战斗/晖暮.png",
    },
}
