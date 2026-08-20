"""Tests for action.combat.core.team."""

from __future__ import annotations

from action.combat.core.team import (
    GENERIC_CLS_NAME,
    TEAM_ROSTER_NODE,
    TeamSnapshot,
    entry_qte_bench_colors,
    generic_team_roster,
    is_generic_team_roster,
    load_team_roster_from_context,
    publish_team_roster,
    role_display_name_to_cls,
    roster_from_entry_qte,
    roster_from_role_selection,
    should_infer_team_size_from_qte,
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

    def test_is_generic_team_roster_true_when_only_one_slot(self):
        assert is_generic_team_roster({"R": GENERIC_CLS_NAME, "B": "", "Y": ""}) is True

    def test_is_generic_team_roster_false_when_empty(self):
        assert is_generic_team_roster({"R": "", "B": "", "Y": ""}) is False


class TestShouldInferTeamSizeFromQte:
    def test_none_or_empty_infers(self):
        assert should_infer_team_size_from_qte(None) is True
        assert should_infer_team_size_from_qte({"R": "", "B": "", "Y": ""}) is True

    def test_all_general_fight_infers(self):
        assert should_infer_team_size_from_qte(generic_team_roster()) is True
        assert should_infer_team_size_from_qte(
            {"R": GENERIC_CLS_NAME, "B": "", "Y": ""}
        ) is True

    def test_any_specialized_skips(self):
        assert should_infer_team_size_from_qte(
            {"R": "Oblivion", "B": "Spectre", "Y": "Aeternion"}
        ) is False
        assert should_infer_team_size_from_qte(
            {"R": "InverseCrown", "B": GENERIC_CLS_NAME, "Y": GENERIC_CLS_NAME}
        ) is False


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


class TestRosterFromEntryQte:
    def test_no_qte_is_solo_red(self):
        roster = roster_from_entry_qte("Oblivion", ["R"], generic_team_roster())
        assert roster == {"R": "Oblivion", "B": "", "Y": ""}

    def test_one_blue_qte_is_duo(self):
        roster = roster_from_entry_qte("Oblivion", ["B"], generic_team_roster())
        assert roster == {
            "R": "Oblivion",
            "B": GENERIC_CLS_NAME,
            "Y": "",
        }

    def test_yellow_and_blue_qte_is_trio(self):
        published = {
            "R": GENERIC_CLS_NAME,
            "B": "Spectre",
            "Y": "Aeternion",
        }
        roster = roster_from_entry_qte("Oblivion", ["Y", "B"], published)
        assert roster == {"R": "Oblivion", "B": "Spectre", "Y": "Aeternion"}

    def test_empty_published_uses_generic_placeholders(self):
        roster = roster_from_entry_qte("Hyperreal", ["B", "Y"], None)
        assert roster == {
            "R": "Hyperreal",
            "B": GENERIC_CLS_NAME,
            "Y": GENERIC_CLS_NAME,
        }

    def test_empty_field_cls_falls_back_to_generic(self):
        roster = roster_from_entry_qte("", [], None)
        assert roster == {"R": GENERIC_CLS_NAME, "B": "", "Y": ""}


class TestEntryQteBenchColors:
    def test_ignores_red_and_keeps_by_order(self):
        assert entry_qte_bench_colors(["R", "Y", "B"]) == ("B", "Y")
        assert entry_qte_bench_colors(["Y"]) == ("Y",)
        assert entry_qte_bench_colors([]) == ()


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
