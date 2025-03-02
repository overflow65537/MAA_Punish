from enum import Enum


class ActionStatusEnum(Enum):
    invalid = 0
    pending = 1000
    running = 2000
    succeeded = 3000
    failed = 4000
    done = 5000


class TaskNameEnum(Enum):
    attack = 1
    dodge = 2
    use_skill = 3
    ball_elimination = 4
    trigger_qte_first = 5
    trigger_qte_second = 6
