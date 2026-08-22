"""Tests for CombatTask.refresh_field_role (idle and non-idle)."""

from __future__ import annotations

from dataclasses import dataclass

from action.combat.core.provider import BaseCombatCheck
from action.combat.core.role_factory import create_role
from action.combat.core.session import CombatTask
from action.combat.core.team import TeamSnapshot

from test_support.fakes import FakeContext, make_hit, make_miss


@dataclass
class _FixedTeamCheck(BaseCombatCheck):
    snapshot: TeamSnapshot

    def detect_team(self, context, combat):
        return self.snapshot

    def in_combat(self, context, combat) -> bool:
        return True

    def in_outer_interface(self, context, combat) -> bool:
        return False


def _combat_with_team(
    snapshot: TeamSnapshot, *, dodge_visible: bool = True
) -> CombatTask:
    dodge = make_hit() if dodge_visible else make_miss()
    combat = CombatTask(
        FakeContext(recognition_map={"检查闪避": dodge}),
        _FixedTeamCheck(snapshot),
    )
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

    def test_mismatch_prefers_teammates_and_skips_current(self, monkeypatch):
        combat = _combat_with_team(
            TeamSnapshot(R="Geiravor", B="", Y="Aeternion", current="R")
        )
        combat._last_field_cls = "Geiravor"
        role = combat.roles["R"]
        captured: dict[str, object] = {}

        monkeypatch.setattr(
            "action.combat.core.session.is_cls_on_field",
            lambda *_args, **_kwargs: False,
        )

        def fake_detect(*_args, **kwargs):
            captured.update(kwargs)
            return ("不落日", "Aeternion")

        monkeypatch.setattr(
            "action.combat.core.session.detect_current_role",
            fake_detect,
        )

        assert combat.refresh_field_role(role) is True
        assert captured.get("prefer_cls") == ["Aeternion"]
        assert captured.get("skip_cls") == ("Geiravor",)
        on_tick = captured.get("on_tick")
        assert callable(on_tick)
        assert on_tick.__func__ is CombatTask._blind_attack_tick
        assert on_tick.__self__ is combat
        assert combat._last_field_cls == "Aeternion"

    def test_hit_records_last_field_cls(self, monkeypatch):
        combat = _combat_with_team(
            TeamSnapshot(R="Geiravor", B="", Y="Aeternion", current="R")
        )
        role = combat.roles["R"]
        monkeypatch.setattr(
            "action.combat.core.session.is_cls_on_field",
            lambda *_args, **_kwargs: True,
        )
        detect_calls = {"n": 0}

        def fake_detect(*_args, **_kwargs):
            detect_calls["n"] += 1
            return ("灼惘", "Geiravor")

        monkeypatch.setattr(
            "action.combat.core.session.detect_current_role",
            fake_detect,
        )
        assert combat.refresh_field_role(role) is False
        assert detect_calls["n"] == 0
        assert combat._last_field_cls == "Geiravor"

    def test_skips_when_dodge_button_missing(self, monkeypatch):
        combat = _combat_with_team(
            TeamSnapshot(R="Geiravor", B="", Y="Aeternion", current="R"),
            dodge_visible=False,
        )
        role = combat.roles["R"]
        field_calls = {"n": 0}
        detect_calls = {"n": 0}

        def fake_field(*_args, **_kwargs):
            field_calls["n"] += 1
            return False

        def fake_detect(*_args, **_kwargs):
            detect_calls["n"] += 1
            return ("不落日", "Aeternion")

        monkeypatch.setattr(
            "action.combat.core.session.is_cls_on_field",
            fake_field,
        )
        monkeypatch.setattr(
            "action.combat.core.session.detect_current_role",
            fake_detect,
        )

        assert combat.refresh_field_role(role) is False
        assert field_calls["n"] == 0
        assert detect_calls["n"] == 0
        assert combat.team is not None
        assert combat.team.current == "R"
