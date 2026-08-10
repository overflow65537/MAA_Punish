"""Tests for solo-team field vs roster reconciliation at combat entry."""

from __future__ import annotations

from dataclasses import dataclass

from action.combat.core.provider import BaseCombatCheck
from action.combat.core.role_factory import create_role
from action.combat.core.session import CombatTask
from action.combat.core.team import TeamSnapshot

from test_support.fakes import FakeContext


@dataclass
class _FixedTeamCheck(BaseCombatCheck):
    snapshot: TeamSnapshot

    def detect_team(self, context, combat):
        return self.snapshot

    def in_combat(self, context, combat) -> bool:
        return True

    def in_outer_interface(self, context, combat) -> bool:
        return False

    def match_exit_overlay(self, context, combat) -> bool:
        return False

    def detect_qte_colors(self, context, combat) -> list[str]:
        return []

    def check_battle_state(self, context, combat) -> str:
        return "unknown"

    def combat_end_condition(self, context, combat) -> bool:
        return False

    def on_combat_check(self, context, combat) -> bool:
        return True


def _combat_with_team(snapshot: TeamSnapshot) -> CombatTask:
    combat = CombatTask(FakeContext(), _FixedTeamCheck(snapshot))
    combat.team = snapshot
    combat.roles = {
        color: create_role(combat, color, snapshot.cls_at(color))
        for color in ("R", "B", "Y")
        if snapshot.cls_at(color)
    }
    return combat


class TestSoloFieldRosterReconcile:
    def test_solo_mismatch_rebinds_to_dedicated_field_character(self, monkeypatch):
        combat = _combat_with_team(TeamSnapshot.solo("Shukra"))
        monkeypatch.setattr(
            "action.combat.core.session.detect_current_role",
            lambda *_args, **_kwargs: ("专属", "Spectre"),
        )
        monkeypatch.setattr(
            "action.combat.core.session.is_cls_on_field",
            lambda *_args, **_kwargs: False,
        )

        display, cls_name = combat._correct_role_from_field(
            "R", "Shukra", b"img", solo=True
        )

        assert display == "专属"
        assert cls_name == "Spectre"
        assert combat.team.R == "Spectre"
        assert combat.roles["R"].cls_name == "Spectre"

    def test_solo_mismatch_rebinds_general_fight_on_field(self, monkeypatch):
        """回音等通用 cls 角色：roster 为专属但场上仍是旧通用角色。"""
        combat = _combat_with_team(TeamSnapshot.solo("Shukra"))
        monkeypatch.setattr(
            "action.combat.core.session.detect_current_role",
            lambda *_args, **_kwargs: ("回音", "GeneralFight"),
        )
        monkeypatch.setattr(
            "action.combat.core.session.is_cls_on_field",
            lambda *_args, **_kwargs: False,
        )

        display, cls_name = combat._correct_role_from_field(
            "R", "Shukra", b"img", solo=True
        )

        assert display == "回音"
        assert cls_name == "GeneralFight"
        assert combat.team.R == "GeneralFight"
        assert combat.roles["R"].cls_name == "GeneralFight"

    def test_solo_keeps_roster_when_roster_on_field(self, monkeypatch):
        combat = _combat_with_team(TeamSnapshot.solo("Shukra"))
        monkeypatch.setattr(
            "action.combat.core.session.detect_current_role",
            lambda *_args, **_kwargs: ("回音", "GeneralFight"),
        )
        monkeypatch.setattr(
            "action.combat.core.session.is_cls_on_field",
            lambda _ctx, _img, cls_name: cls_name == "Shukra",
        )

        display, cls_name = combat._correct_role_from_field(
            "R", "Shukra", b"img", solo=True
        )

        assert cls_name == "Shukra"
        assert combat.team.R == "Shukra"
        assert display == "回音"

    def test_multi_team_mismatch_keeps_roster_strategy(self, monkeypatch):
        combat = _combat_with_team(
            TeamSnapshot(R="Shukra", B="GeneralFight", Y="", current="R")
        )
        monkeypatch.setattr(
            "action.combat.core.session.detect_current_role",
            lambda *_args, **_kwargs: ("回音", "GeneralFight"),
        )

        display, cls_name = combat._correct_role_from_field(
            "R", "Shukra", b"img", solo=False
        )

        assert cls_name == "Shukra"
        assert combat.team.R == "Shukra"

    def test_load_team_applies_solo_reconcile_for_echo_on_field(self, monkeypatch):
        combat = CombatTask(
            FakeContext(), _FixedTeamCheck(TeamSnapshot.solo("Shukra"))
        )
        combat.frame = b"img"
        monkeypatch.setattr(
            "action.combat.core.session.detect_current_role",
            lambda *_args, **_kwargs: ("回音", "GeneralFight"),
        )
        monkeypatch.setattr(
            "action.combat.core.session.is_cls_on_field",
            lambda *_args, **_kwargs: False,
        )

        assert combat.load_team() is True
        assert combat.team is not None
        assert combat.team.R == "GeneralFight"
        role = combat.get_current_role()
        assert role is not None
        assert role.cls_name == "GeneralFight"
        assert combat.current_role_name == "回音"
