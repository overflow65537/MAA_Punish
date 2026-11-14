"""Tests for ClickAnchor：9 个基准点 + 带符号 (x, y) 偏移。"""

from __future__ import annotations

import json

import pytest

from action.basics.ClickAnchor import ClickAnchor
from maa.custom_action import CustomAction
from maa.define import Rect
from test_support.fakes import FakeContext

# x, y, w, h —— w//2 = 20，h//2 = 10，结果都是整数便于断言
BOX = (100, 200, 41, 21)

EXPECTED = {
    "top_left": (100, 200),
    "top": (120, 200),
    "top_right": (141, 200),
    "left": (100, 210),
    "center": (120, 210),
    "right": (141, 210),
    "bottom_left": (100, 221),
    "bottom": (120, 221),
    "bottom_right": (141, 221),
}


def click(param, box=BOX):
    context = FakeContext()
    argv = CustomAction.RunArg(
        task_detail=None,
        node_name="战斗_点右缘",
        custom_action_name="ClickAnchor",
        custom_action_param=json.dumps(param),
        reco_detail=None,
        box=Rect(*box),
    )
    result = ClickAnchor().run(context, argv)
    return result.success, context.tasker.controller.clicks


@pytest.mark.parametrize("position,expected", sorted(EXPECTED.items()))
def test_nine_positions(position, expected):
    assert click({"position": position}) == (True, [expected])


@pytest.mark.parametrize(
    "position,x,y,expected",
    [
        ("right", -6, 3, (135, 213)),
        ("right", 10, 0, (151, 210)),
        ("left", -10, 0, (90, 210)),
        ("top", 0, 5, (120, 205)),
        ("bottom", 0, -5, (120, 216)),
        ("center", -6, 3, (114, 213)),
        ("bottom_right", -6, -6, (135, 215)),
    ],
)
def test_offset_signs(position, x, y, expected):
    assert click({"position": position, "x": x, "y": y}) == (True, [expected])


def test_defaults_to_center():
    assert click({}) == (True, [EXPECTED["center"]])


def test_only_x_given():
    assert click({"position": "left", "x": 7}) == (True, [(107, 210)])


def test_unknown_position_fails_without_clicking():
    assert click({"position": "diagonal"}) == (False, [])


def test_nine_points_are_distinct():
    assert len(set(EXPECTED.values())) == 9
