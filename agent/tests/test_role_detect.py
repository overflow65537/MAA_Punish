"""Tests for action.combat.core.role_detect."""

from __future__ import annotations

from action.combat.core import role_detect
from action.combat.core.role_detect import (
    attack_templates_for_cls,
    detect_current_role,
    is_dodge_button_visible,
    is_switch_arrived,
    match_attack_template,
    ordered_role_entries,
)

from test_support.fakes import FakeContext, make_hit, make_miss

MINI_ROLE_ACTIONS = {
    "专属·测试": {
        "name": "专属",
        "cls_name": "Spectre",
        "attack_template": ["自定义战斗/专属.png"],
    },
    "通用·测试": {
        "name": "通用",
        "cls_name": "GeneralFight",
        "attack_template": ["自定义战斗/通用.png"],
    },
}


class TestAttackTemplatesForCls:
    def test_known_cls_returns_templates(self):
        templates = attack_templates_for_cls("InverseCrown")
        assert templates
        assert isinstance(templates, list)

    def test_unknown_cls_returns_empty(self):
        assert attack_templates_for_cls("NotARealRole") == []


class TestMatchAttackTemplate:
    def test_empty_templates_returns_false(self):
        context = FakeContext()
        assert match_attack_template(context, b"img", []) is False
        assert context.check_role_calls == []

    def test_passes_pipeline_override_with_matching_threshold_count(self):
        context = FakeContext(check_role_results=[make_hit()])
        templates = ["a.png", "b.png"]
        assert match_attack_template(context, b"img", templates) is True
        assert len(context.check_role_calls) == 1
        override = context.check_role_calls[0]["pipeline_override"]
        param = override["检查角色"]["recognition"]["param"]
        assert param["template"] == templates
        assert param["threshold"] == [0.8, 0.8]


class TestDetectCurrentRole:
    def setup_method(self, method):
        self._original = role_detect.ROLE_ACTIONS

    def teardown_method(self, method):
        role_detect.ROLE_ACTIONS = self._original

    def test_dedicated_role_wins_over_general_fight(self, monkeypatch):
        monkeypatch.setattr(role_detect, "ROLE_ACTIONS", MINI_ROLE_ACTIONS)
        context = FakeContext(
            check_role_results=[make_hit(), make_miss(), make_miss()]
        )
        display, cls_name = detect_current_role(context, b"img")
        assert display == "专属"
        assert cls_name == "Spectre"

    def test_general_fight_when_only_generic_matches(self, monkeypatch):
        monkeypatch.setattr(role_detect, "ROLE_ACTIONS", MINI_ROLE_ACTIONS)
        context = FakeContext(check_role_results=[make_miss(), make_hit()])
        display, cls_name = detect_current_role(context, b"img")
        assert display == "通用"
        assert cls_name == "GeneralFight"

    def test_unknown_when_no_match(self, monkeypatch):
        monkeypatch.setattr(role_detect, "ROLE_ACTIONS", MINI_ROLE_ACTIONS)
        context = FakeContext(check_role_results=[make_miss(), make_miss()])
        display, cls_name = detect_current_role(context, b"img")
        assert display == "未知"
        assert cls_name == "GeneralFight"

    def test_on_tick_called_before_each_attempt(self, monkeypatch):
        monkeypatch.setattr(role_detect, "ROLE_ACTIONS", MINI_ROLE_ACTIONS)
        context = FakeContext(check_role_results=[make_miss(), make_hit()])
        ticks: list[int] = []

        detect_current_role(context, b"img", on_tick=lambda: ticks.append(1))
        assert len(ticks) == 2

    def test_prefer_cls_is_scanned_before_catalog(self, monkeypatch):
        monkeypatch.setattr(role_detect, "ROLE_ACTIONS", MINI_ROLE_ACTIONS)
        context = FakeContext(check_role_results=[make_hit()])
        display, cls_name = detect_current_role(
            context, b"img", prefer_cls=["GeneralFight"]
        )
        assert display == "通用"
        assert cls_name == "GeneralFight"
        assert len(context.check_role_calls) == 1
        templates = context.check_role_calls[0]["pipeline_override"]["检查角色"][
            "recognition"
        ]["param"]["template"]
        assert templates == ["自定义战斗/通用.png"]

    def test_skip_cls_omits_already_checked_role(self, monkeypatch):
        monkeypatch.setattr(role_detect, "ROLE_ACTIONS", MINI_ROLE_ACTIONS)
        context = FakeContext(check_role_results=[make_hit()])
        display, cls_name = detect_current_role(
            context, b"img", skip_cls=["Spectre"]
        )
        assert display == "通用"
        assert cls_name == "GeneralFight"
        assert len(context.check_role_calls) == 1

    def test_ordered_entries_prefer_then_rest(self, monkeypatch):
        monkeypatch.setattr(role_detect, "ROLE_ACTIONS", MINI_ROLE_ACTIONS)
        names = [name for name, _info in ordered_role_entries(prefer_cls=["GeneralFight"])]
        assert names == ["通用·测试", "专属·测试"]


class TestIsSwitchArrived:
    def setup_method(self, method):
        self._original = role_detect.ROLE_ACTIONS

    def teardown_method(self, method):
        role_detect.ROLE_ACTIONS = self._original

    def test_specific_cls_uses_target_template_only(self, monkeypatch):
        monkeypatch.setattr(role_detect, "ROLE_ACTIONS", MINI_ROLE_ACTIONS)
        context = FakeContext(check_role_results=[make_hit()])
        assert is_switch_arrived(context, b"img", "Spectre") is True
        assert len(context.check_role_calls) == 1

    def test_general_fight_arrives_when_dedicated_on_field(self, monkeypatch):
        monkeypatch.setattr(role_detect, "ROLE_ACTIONS", MINI_ROLE_ACTIONS)
        context = FakeContext(
            check_role_results=[make_miss(), make_hit(), make_miss()]
        )
        assert is_switch_arrived(context, b"img", "GeneralFight") is True

    def test_general_fight_not_arrived_when_unknown(self, monkeypatch):
        monkeypatch.setattr(role_detect, "ROLE_ACTIONS", MINI_ROLE_ACTIONS)
        context = FakeContext(check_role_results=[make_miss(), make_miss()])
        assert is_switch_arrived(context, b"img", "GeneralFight") is False


class TestIsDodgeButtonVisible:
    def test_hit(self):
        context = FakeContext(recognition_map={"检查闪避": make_hit()})
        assert is_dodge_button_visible(context, b"img") is True

    def test_miss(self):
        context = FakeContext(recognition_map={"检查闪避": make_miss()})
        assert is_dodge_button_visible(context, b"img") is False
