"""Tests for CombatTask.refresh_field_role (idle and non-idle)."""

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


def _combat_with_team(snapshot: TeamSnapshot) -> CombatTask:
    combat = CombatTask(FakeContext(), _FixedTeamCheck(snapshot))
    combat.team = snapshot
    combat.frame = b"img"
    combat.roles = {
        color: create_role(combat, color, snapshot.cls_at(color))
        for color in ("R", "B", "Y")
        if snapshot.cls_at(color)
    }
    return combat


class TestRefreshFieldRole:
    def test_perform_checks_field_outside_idle(self, monkeypatch):
        combat = _combat_with_team(
            TeamSnapshot(R="Geiravor", B="", Y="GeneralFight", current="R")
        )
        role = combat.roles["R"]
        role.phase = "p2"
        seen: list[str] = []

        def fake_refresh(_role):
            seen.append(_role.phase)
            return False

        monkeypatch.setattr(combat, "refresh_field_role", fake_refresh)
        monkeypatch.setattr(role, "do_perform", lambda: seen.append("do"))
        role.perform()
        assert seen == ["p2", "do"]

    def test_p2_mismatch_adopts_bench_general_fight(self, monkeypatch):
        combat = _combat_with_team(
            TeamSnapshot(R="Geiravor", B="", Y="GeneralFight", current="R")
        )
        role = combat.roles["R"]
        role.phase = "p2"
        monkeypatch.setattr(
            "action.combat.core.session.is_cls_on_field",
            lambda *_args, **_kwargs: False,
        )
        monkeypatch.setattr(
            "action.combat.core.session.detect_current_role",
            lambda *_args, **_kwargs: ("不落日", "Aeternion"),
        )

        assert combat.refresh_field_role(role) is True
        assert combat.team is not None
        assert combat.team.current == "Y"
        assert combat.team.Y == "Aeternion"
        assert combat.roles["Y"].cls_name == "Aeternion"
        assert combat.roles["Y"].phase == "idle"

    def test_keeps_going_when_expected_cls_on_field(self, monkeypatch):
        combat = _combat_with_team(
            TeamSnapshot(R="Geiravor", B="", Y="GeneralFight", current="R")
        )
        role = combat.roles["R"]
        role.phase = "p2"
        monkeypatch.setattr(
            "action.combat.core.session.is_cls_on_field",
            lambda *_args, **_kwargs: True,
        )
        assert combat.refresh_field_role(role) is False
        assert combat.team is not None
        assert combat.team.current == "R"
        assert role.phase == "p2"

    def test_solo_rebinds_current_when_field_changes(self, monkeypatch):
        combat = _combat_with_team(TeamSnapshot.solo("GeneralFight"))
        role = combat.roles["R"]
        role.phase = "farm"
        monkeypatch.setattr(
            "action.combat.core.session.is_cls_on_field",
            lambda *_args, **_kwargs: False,
        )
        monkeypatch.setattr(
            "action.combat.core.session.detect_current_role",
            lambda *_args, **_kwargs: ("不落日", "Aeternion"),
        )
        assert combat.refresh_field_role(role) is True
        assert combat.team is not None
        assert combat.team.R == "Aeternion"
        assert combat.roles["R"].cls_name == "Aeternion"
