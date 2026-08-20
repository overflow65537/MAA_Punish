"""Tests for CombatCheck.detect_team entry QTE sizing."""

from __future__ import annotations

from dataclasses import dataclass

from action.combat.core.provider import CombatCheck
from action.combat.core.team import GENERIC_CLS_NAME, TEAM_ROSTER_NODE

from test_support.fakes import FakeContext


@dataclass
class _FakeCombat:
    frame: bytes = b"img"
    current_role_name: str = ""


def _detect_team(
    monkeypatch,
    visible,
    field_cls="Oblivion",
    published=None,
    *,
    track_detect=None,
):
    check = CombatCheck()
    context = FakeContext()
    if published is not None:
        context.node_data[TEAM_ROSTER_NODE] = {"attach": published}

    detect_calls = {"n": 0}

    def fake_detect(*_args, **_kwargs):
        detect_calls["n"] += 1
        return ("终焉", field_cls)

    monkeypatch.setattr(
        "action.combat.core.provider.detect_visible_team_colors",
        lambda *_args, **_kwargs: visible,
    )
    monkeypatch.setattr(
        "action.combat.core.provider.detect_current_role",
        fake_detect,
    )
    snap = check.detect_team(context, _FakeCombat())
    if track_detect is not None:
        track_detect["n"] = detect_calls["n"]
    return snap


class TestDetectTeamByEntryQte:
    def test_no_bench_qte_is_solo_red(self, monkeypatch):
        snap = _detect_team(monkeypatch, visible=["R"])
        assert snap is not None
        assert snap.current == "R"
        assert snap.R == "Oblivion"
        assert snap.B == ""
        assert snap.Y == ""
        assert snap.is_solo() is True

    def test_one_blue_qte_is_duo(self, monkeypatch):
        snap = _detect_team(monkeypatch, visible=["B"])
        assert snap is not None
        assert snap.filled_colors() == ("R", "B")
        assert snap.B == GENERIC_CLS_NAME
        assert snap.is_solo() is False

    def test_generic_published_with_two_qte_is_trio(self, monkeypatch):
        snap = _detect_team(
            monkeypatch,
            visible=["B", "Y"],
            published={
                "R": GENERIC_CLS_NAME,
                "B": GENERIC_CLS_NAME,
                "Y": GENERIC_CLS_NAME,
            },
        )
        assert snap is not None
        assert snap.filled_colors() == ("R", "B", "Y")
        assert snap.R == "Oblivion"
        assert snap.B == GENERIC_CLS_NAME
        assert snap.Y == GENERIC_CLS_NAME

    def test_specialized_roster_skips_qte_and_uses_selection(self, monkeypatch):
        calls = {}
        snap = _detect_team(
            monkeypatch,
            visible=[],
            field_cls="Hyperreal",
            published={
                "R": "Oblivion",
                "B": "Spectre",
                "Y": "Aeternion",
            },
            track_detect=calls,
        )
        assert snap is not None
        assert snap.R == "Oblivion"
        assert snap.B == "Spectre"
        assert snap.Y == "Aeternion"
        assert calls["n"] == 0

    def test_mixed_specialized_skips_qte(self, monkeypatch):
        snap = _detect_team(
            monkeypatch,
            visible=["B"],
            published={
                "R": "InverseCrown",
                "B": GENERIC_CLS_NAME,
                "Y": GENERIC_CLS_NAME,
            },
        )
        assert snap is not None
        assert snap.R == "InverseCrown"
        assert snap.B == GENERIC_CLS_NAME
        assert snap.Y == GENERIC_CLS_NAME

    def test_empty_published_with_two_qte_uses_generic_bench(self, monkeypatch):
        snap = _detect_team(monkeypatch, visible=["Y", "B"], published=None)
        assert snap is not None
        assert snap.B == GENERIC_CLS_NAME
        assert snap.Y == GENERIC_CLS_NAME
        assert snap.current == "R"

    def test_qte_check_runs_after_field_role_detect(self, monkeypatch):
        order: list[str] = []

        def fake_detect(*_args, **_kwargs):
            order.append("role")
            return ("终焉", "Oblivion")

        def fake_qte(*_args, **_kwargs):
            order.append("qte")
            return ["B", "Y"]

        monkeypatch.setattr(
            "action.combat.core.provider.detect_current_role",
            fake_detect,
        )
        monkeypatch.setattr(
            "action.combat.core.provider.detect_visible_team_colors",
            fake_qte,
        )
        snap = CombatCheck().detect_team(FakeContext(), _FakeCombat())
        assert order == ["role", "qte"]
        assert snap is not None
        assert snap.filled_colors() == ("R", "B", "Y")
