"""主线章节内"关卡锚点"推进的单元测试。

覆盖两条不依赖实机画面的纯逻辑：
- MainStoryInitStage：从一次 OCR 结果里挑出当前关，并把锚点设好
- MainStoryAdvance：按锚点把关卡序号 +1，到章末切到"退出本章"
"""

from __future__ import annotations

import json

import pytest

from action.main_story.stage_anchor import (
    ANCHOR_ADVANCE,
    ANCHOR_STAGE,
    MainStoryAdvance,
    MainStoryInitStage,
)
from test_support.fakes import FakeBestResult, FakeContext, FakeRecognitionResult


class _Arg:
    def __init__(self, param: dict, image=None):
        raw = json.dumps(param, ensure_ascii=False)
        self.custom_action_param = raw
        self.custom_recognition_param = raw
        self.image = image
        self.node_name = ""


def _ocr_result(texts: list[str]) -> FakeRecognitionResult:
    boxes = [
        FakeBestResult(box=(100 + 20 * i, 300, 60, 20), text=text)
        for i, text in enumerate(texts)
    ]
    return FakeRecognitionResult(hit=bool(boxes), best_result=boxes[0] if boxes else None,
                                 filtered_results=boxes, all_results=boxes)


def _init_param(stages: int = 13) -> dict:
    return {"chapter": "09", "label_prefix": "9", "stages": stages}


def _advance_param(stages: int = 13) -> dict:
    return {"chapter": "09", "label_prefix": "9", "stages": stages}


# ---------------------------------------------------------------- init

def test_init_picks_highest_visible_stage():
    ctx = FakeContext()
    ctx.recognition_map["主线_关卡列表"] = _ocr_result(["9-1", "9-8", "9-13", "序章"])

    result = MainStoryInitStage().analyze(ctx, _Arg(_init_param()))

    assert ctx.anchors[ANCHOR_STAGE] == "09_13"
    assert ctx.anchors[ANCHOR_ADVANCE] == "推进关卡_09"
    assert result is not None and result.detail["stage"] == 13


def test_init_falls_back_to_first_stage_when_nothing_matches():
    ctx = FakeContext()
    ctx.recognition_map["主线_关卡列表"] = _ocr_result(["主线", "序章"])

    result = MainStoryInitStage().analyze(ctx, _Arg(_init_param()))

    assert ctx.anchors[ANCHOR_STAGE] == "09_01"
    assert result is not None


def test_init_clamps_out_of_table_stage():
    """OCR 把 9-1 和 13 拼成 9-113 之类的噪声时，别把锚点设到表外节点。"""
    ctx = FakeContext()
    ctx.recognition_map["主线_关卡列表"] = _ocr_result(["9-113"])

    result = MainStoryInitStage().analyze(ctx, _Arg(_init_param(stages=13)))

    assert ctx.anchors[ANCHOR_STAGE] == "09_13"
    assert result is not None


def test_init_ignores_other_chapters_labels():
    ctx = FakeContext()
    ctx.recognition_map["主线_关卡列表"] = _ocr_result(["10-9", "9-3"])

    MainStoryInitStage().analyze(ctx, _Arg(_init_param()))

    assert ctx.anchors[ANCHOR_STAGE] == "09_03"


# ------------------------------------------------------------- advance

def test_advance_walks_forward():
    ctx = FakeContext()
    ctx.anchors[ANCHOR_STAGE] = "09_07"

    MainStoryAdvance().run(ctx, _Arg(_advance_param()))

    assert ctx.anchors[ANCHOR_STAGE] == "09_08"


def test_advance_exits_chapter_after_last_stage():
    ctx = FakeContext()
    ctx.anchors[ANCHOR_STAGE] = "09_13"

    MainStoryAdvance().run(ctx, _Arg(_advance_param()))

    assert ctx.anchors[ANCHOR_STAGE] == "退出本章_09"


def test_advance_is_noop_without_anchor():
    """旧流程（未接入锚点）不设锚点，推进必须什么都不做。"""
    ctx = FakeContext()

    result = MainStoryAdvance().run(ctx, _Arg(_advance_param()))

    assert result.success is True
    assert ctx.anchors == {}


def test_advance_is_noop_for_foreign_chapter():
    ctx = FakeContext()
    ctx.anchors[ANCHOR_STAGE] = "10_03"

    MainStoryAdvance().run(ctx, _Arg(_advance_param()))

    assert ctx.anchors[ANCHOR_STAGE] == "10_03"


def test_advance_bad_param_does_not_raise():
    ctx = FakeContext()
    ctx.anchors[ANCHOR_STAGE] = "09_02"

    MainStoryAdvance().run(ctx, _Arg({"chapter": "09", "stages": "not-a-number"}))

    assert ctx.anchors[ANCHOR_STAGE] == "09_03"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
