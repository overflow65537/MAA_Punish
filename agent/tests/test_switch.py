"""Tests for action.combat.core.switch."""

from __future__ import annotations

from action.combat.core import switch
from action.combat.core.switch import (
    _ATTACK_CLICK,
    attempt_switch_to_color,
    blind_attack_click,
    click_qte_by_color,
    click_qte_until_done,
    detect_visible_team_colors,
)

from test_support.fakes import FakeContext, make_hit, make_miss


class TestBlindAttackClick:
    def test_posts_attack_coordinates(self):
        context = FakeContext()
        blind_attack_click(context)
        assert context.tasker.controller.clicks == [_ATTACK_CLICK]


class TestDetectVisibleTeamColors:
    def test_sorts_by_vertical_position(self):
        context = FakeContext(
            recognition_map={
                "切换红色QTE": make_hit((0, 300, 40, 40)),
                "切换蓝色QTE": make_hit((0, 100, 40, 40)),
                "切换黄色QTE": make_hit((0, 200, 40, 40)),
            }
        )
        assert detect_visible_team_colors(context, b"img") == ["B", "Y", "R"]


class TestClickQteByColor:
    def test_clicks_when_qte_visible(self):
        context = FakeContext(
            recognition_map={"切换红色QTE": make_hit((100, 200, 40, 40))}
        )
        assert click_qte_by_color(context, "R", b"img", burst=2) is True
        assert context.tasker.controller.clicks == [(120, 220), (120, 220)]

    def test_returns_false_when_qte_missing(self):
        context = FakeContext(recognition_map={"切换红色QTE": make_miss()})
        assert click_qte_by_color(context, "R", b"img") is False
        assert context.tasker.controller.clicks == []


class TestAttemptSwitchToColor:
    def test_already_arrived_returns_true_without_qte_click(self, monkeypatch):
        context = FakeContext()
        monkeypatch.setattr(
            switch,
            "is_switch_arrived",
            lambda _ctx, _img, cls_name: cls_name == "Spectre",
        )
        assert attempt_switch_to_color(context, "R", "Spectre") is True
        assert context.tasker.controller.clicks == []

    def test_returns_false_when_qte_not_found(self, monkeypatch):
        context = FakeContext(recognition_map={"切换红色QTE": make_miss()})
        monkeypatch.setattr(switch, "is_switch_arrived", lambda *_args: False)
        assert attempt_switch_to_color(context, "R", "Spectre") is False

    def test_succeeds_after_qte_click(self, monkeypatch):
        context = FakeContext(
            recognition_map={"切换红色QTE": make_hit((100, 200, 40, 40))}
        )
        calls = {"n": 0}

        def fake_arrived(_ctx, _img, cls_name):
            calls["n"] += 1
            return calls["n"] >= 2 and cls_name == "Spectre"

        monkeypatch.setattr(switch, "is_switch_arrived", fake_arrived)
        monkeypatch.setattr(switch.time, "monotonic", lambda: 0.0)
        monkeypatch.setattr(switch.time, "sleep", lambda _s: None)

        assert attempt_switch_to_color(
            context,
            "R",
            "Spectre",
            verify_timeout=5.0,
            poll_interval=0.01,
        ) is True
        assert context.tasker.controller.clicks

    def test_times_out_when_never_arrives(self, monkeypatch):
        context = FakeContext(
            recognition_map={"切换红色QTE": make_hit((100, 200, 40, 40))}
        )
        monkeypatch.setattr(switch, "is_switch_arrived", lambda *_args: False)

        clock = {"t": 0.0}

        def monotonic():
            clock["t"] += 1.0
            return clock["t"]

        monkeypatch.setattr(switch.time, "monotonic", monotonic)
        monkeypatch.setattr(switch.time, "sleep", lambda _s: None)

        assert (
            attempt_switch_to_color(
                context,
                "R",
                "Spectre",
                verify_timeout=2.0,
                poll_interval=0.01,
            )
            is False
        )


class TestClickQteUntilDone:
    def test_returns_true_when_qte_disappears(self, monkeypatch):
        context = FakeContext(
            recognition_map={
                "切换红色QTE": make_hit((100, 200, 40, 40)),
            }
        )
        seen = {"n": 0}

        def fake_recognize(_ctx, _color, _image):
            seen["n"] += 1
            if seen["n"] == 1:
                return make_hit((100, 200, 40, 40))
            return None

        monkeypatch.setattr(switch, "_recognize_qte", fake_recognize)
        monkeypatch.setattr(
            switch,
            "active_delay",
            lambda *_args, **_kwargs: True,
        )
        assert click_qte_until_done(context, "R", b"img", max_loops=3) is True

    def test_returns_false_when_initial_qte_missing(self):
        context = FakeContext(recognition_map={"切换红色QTE": make_miss()})
        assert click_qte_until_done(context, "R", b"img") is False
