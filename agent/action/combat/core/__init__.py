from action.combat.core.provider import BaseCombatCheck, CombatCheck
from action.combat.core.role import BaseRole, SwitchPriority, resolve_role_name
from action.combat.core.role_detect import detect_current_role
from action.combat.core.role_factory import ROLE_CLASS_MAP, create_role
from action.combat.core.session import CombatTask
from action.combat.core.switch import click_qte_by_color
from action.combat.core.team import TEAM_COLORS, TeamSnapshot

__all__ = [
    "BaseCombatCheck",
    "CombatCheck",
    "CombatTask",
    "BaseRole",
    "SwitchPriority",
    "resolve_role_name",
    "detect_current_role",
    "ROLE_CLASS_MAP",
    "create_role",
    "TeamSnapshot",
    "TEAM_COLORS",
    "click_qte_by_color",
]
