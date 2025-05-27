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
MAA_Punish 战斗人物枚举对象
作者:HCX0426
"""

from enum import Enum


class ActionStatusEnum(Enum):
    INVALID = "无效"
    PENDING = "待处理"
    RUNNING = "运行中"
    SUCCEEDED = "成功"
    FAILED = "失败"
    DONE = "完成"


class GameActionEnum(Enum):
    ATTACK = "攻击"
    DODGE = "闪避"
    USE_SKILL = "技能"
    BALL_ELIMINATION = "消球"
    BALL_ELIMINATION_SECOND = "消球2"
    BALL_ELIMINATION_THREE = "消球3"
    TRIGGER_QTE_FIRST = "1-触发QTE/换人"
    TRIGGER_QTE_SECOND = "2-触发QTE/换人"
    LONG_PRESS_ATTACK = "长按攻击"
    LONG_PRESS_DODGE = "长按闪避"
    LONG_PRESS_SKILL = "长按技能"
    LENS_LOCK = "镜头锁定"
    AUXILIARY_MACHINE = "辅助机"
