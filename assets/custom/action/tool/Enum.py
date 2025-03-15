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
