"""Tests for signal ball layout mapping and elimination strategy."""

from __future__ import annotations

from action.combat.actions.signal_ball_layout import (
    SIGNAL_BALL_SLOT_CENTERS,
    slot_index_from_box,
)
from action.combat.actions.signal_ball_strategy import find_elimination_target


class TestSlotIndexFromBox:
    def test_slot_three_center_maps_to_index_two(self):
        center_x, center_y = SIGNAL_BALL_SLOT_CENTERS[2]
        box = (center_x - 20, center_y - 20, 40, 40)
        assert slot_index_from_box(box) == 2

    def test_invalid_box_returns_minus_one(self):
        assert slot_index_from_box("not-a-box") == -1
        assert slot_index_from_box((0, 0, 1, 1)) == -1


class TestFindEliminationTarget:
    def test_direct_triple_returns_positive_slot(self):
        balls = ["red", "red", "red", None, None, None, None, None]
        assert find_elimination_target(balls) == 1

    def test_move_ball_for_triple_returns_negative_index(self):
        balls = ["red", "blue", "red", "red", None, None, None, None]
        assert find_elimination_target(balls) == -1

    def test_all_empty_returns_zero(self):
        assert find_elimination_target([None] * 8) == 0

    def test_target_red_ignores_non_red_triple(self):
        balls = ["blue", "blue", "blue", None, None, None, None, None]
        assert find_elimination_target(balls, "any") == 1
        assert find_elimination_target(balls, "red") == -1

    def test_target_red_matches_red_triple(self):
        balls = ["red", "red", "red", None, None, None, None, None]
        assert find_elimination_target(balls, "red") == 1
