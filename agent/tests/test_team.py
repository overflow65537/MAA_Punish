"""Tests for action.combat.core.team."""

from __future__ import annotations

from action.combat.core.team import (
    GENERIC_CLS_NAME,
    TEAM_ROSTER_NODE,
    TeamSnapshot,
    generic_team_roster,
    is_generic_team_roster,
    load_team_roster_from_context,
    publish_team_roster,
    role_display_name_to_cls,
    roster_from_role_selection,
)

from test_support.fakes import FakeContext


class TestGenericTeamRoster:
    def test_generic_team_roster_fills_all_colors(self):
        roster = generic_team_roster()
        assert roster == {"R": GENERIC_CLS_NAME, "B": GENERIC_CLS_NAME, "Y": GENERIC_CLS_NAME}

    def test_is_generic_team_roster_true_when_all_general_fight(self):
        assert is_generic_team_roster(generic_team_roster()) is True

    def test_is_generic_team_roster_false_when_mixed(self):
        roster = {"R": "InverseCrown", "B": GENERIC_CLS_NAME, "Y": GENERIC_CLS_NAME}
        assert is_generic_team_roster(roster) is False

    def test_is_generic_team_roster_false_when_only_one_slot(self):
        assert is_generic_team_roster({"R": GENERIC_CLS_NAME, "B": "", "Y": ""}) is False


class TestRoleDisplayNameToCls:
    def test_known_role(self):
        assert role_display_name_to_cls("露西亚·逆冕") == "InverseCrown"

    def test_trial_prefix_stripped(self):
        assert role_display_name_to_cls("[试用]露西亚·逆冕") == "InverseCrown"

    def test_empty_returns_empty(self):
        assert role_display_name_to_cls(None) == ""
        assert role_display_name_to_cls("") == ""
        assert role_display_name_to_cls("[试用]") == ""


class TestRosterFromRoleSelection:
    def test_maps_attacker_tank_support_to_colors(self):
        roster = roster_from_role_selection(
            "露西亚·逆冕",
            "神威·不落日",
            "布偶熊·骇影",
        )
        assert roster["R"] == "InverseCrown"
        assert roster["Y"] == "Aeternion"
        assert roster["B"] == "Spectre"


class TestTeamSnapshot:
    def test_from_dict_valid(self):
        snap = TeamSnapshot.from_dict(
            {"R": "InverseCrown", "B": "Spectre", "Y": "", "current": "R"}
        )
        assert snap is not None
        assert snap.current_cls() == "InverseCrown"
        assert snap.filled_colors() == ("R", "B")
        assert snap.is_solo() is False

    def test_from_dict_missing_field_returns_none(self):
        assert TeamSnapshot.from_dict({"R": "InverseCrown", "B": "", "Y": ""}) is None

    def test_from_dict_invalid_current_returns_none(self):
        assert (
            TeamSnapshot.from_dict(
                {"R": "InverseCrown", "B": "", "Y": "", "current": "X"}
            )
            is None
        )

    def test_from_dict_empty_current_color_cls_returns_none(self):
        assert (
            TeamSnapshot.from_dict(
                {"R": "", "B": "Spectre", "Y": "", "current": "R"}
            )
            is None
        )

    def test_solo_and_helpers(self):
        snap = TeamSnapshot.solo("Hyperreal", current="B")
        assert snap.cls_at("B") == "Hyperreal"
        assert snap.is_solo() is True
        assert snap.other_colors() == ("R", "Y")
        assert snap.other_filled_colors() == ()

    def test_cls_at_invalid_color_raises(self):
        snap = TeamSnapshot.solo("Hyperreal")
        try:
            snap.cls_at("Z")
            assert False, "expected KeyError"
        except KeyError:
            pass


class TestTeamRosterContext:
    def test_publish_and_load_roundtrip(self):
        context = FakeContext()
        roster = {"R": "InverseCrown", "B": "Spectre", "Y": "Aeternion"}
        publish_team_roster(context, roster)

        assert context.pipeline_overrides == [{TEAM_ROSTER_NODE: {"attach": roster}}]
        assert load_team_roster_from_context(context) == roster

    def test_load_returns_none_when_attach_missing(self):
        context = FakeContext()
        assert load_team_roster_from_context(context) is None

    def test_load_returns_none_when_all_empty(self):
        context = FakeContext(
            node_data={TEAM_ROSTER_NODE: {"attach": {"R": "", "B": "", "Y": ""}}}
        )
        assert load_team_roster_from_context(context) is None
