"""主线章节内"关卡锚点"推进的单元测试。

覆盖三条不依赖实机画面的纯逻辑：
- MainStoryInitStage：从一次 OCR 结果里挑出当前关，并把本章锚点设好
- MainStoryAdvance：按本章锚点把关卡序号 +1，到章末切到"退出本章"
- MainStoryRollback：找不到那一关时退回上一关，并受预算约束
"""

from __future__ import annotations

import json

import pytest

from action.main_story import stage_anchor
from action.main_story.stage_anchor import (
    ANCHOR_ADVANCE,
    LEGACY_TAIL,
    MainStoryAdvance,
    MainStoryInitStage,
    MainStoryRollback,
)
from test_support.fakes import FakeBestResult, FakeContext, FakeRecognitionResult

ANCHOR = "09_当前关卡"


@pytest.fixture(autouse=True)
def _clear_rollback_budget():
    """回退预算是模块级状态，逐用例清零，避免互相污染。"""
    stage_anchor._rollbacks.clear()
    yield
    stage_anchor._rollbacks.clear()


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
    return {"anchor": ANCHOR, "chapter": "09", "label_prefix": "9", "stages": stages}


def _advance_param(stages: int = 13) -> dict:
    return {"anchor": ANCHOR, "chapter": "09", "stages": stages}


def _rollback_param() -> dict:
    return {"anchor": ANCHOR, "chapter": "09"}


# ---------------------------------------------------------------- init

def test_init_picks_highest_visible_stage():
    ctx = FakeContext()
    ctx.recognition_map["主线_关卡列表"] = _ocr_result(["9-1", "9-8", "9-13", "序章"])

    result = MainStoryInitStage().analyze(ctx, _Arg(_init_param()))

    assert ctx.anchors[ANCHOR] == "09_13"
    assert ctx.anchors[ANCHOR_ADVANCE] == "推进关卡_09"
    assert result is not None and result.detail["stage"] == 13


def test_init_only_touches_its_own_anchor():
    """第 20 章的锚点不该被第 09 章的初始化覆盖。"""
    ctx = FakeContext()
    ctx.anchors["20_当前关卡"] = "20_07"
    ctx.recognition_map["主线_关卡列表"] = _ocr_result(["9-4"])

    MainStoryInitStage().analyze(ctx, _Arg(_init_param()))

    assert ctx.anchors[ANCHOR] == "09_04"
    assert ctx.anchors["20_当前关卡"] == "20_07"


def test_init_falls_back_to_first_stage_when_nothing_matches():
    ctx = FakeContext()
    ctx.recognition_map["主线_关卡列表"] = _ocr_result(["主线", "序章"])

    result = MainStoryInitStage().analyze(ctx, _Arg(_init_param()))

    assert ctx.anchors[ANCHOR] == "09_01"
    assert result is not None


def test_init_clamps_out_of_table_stage():
    """OCR 把 9-1 和 13 拼成 9-113 之类的噪声时，别把锚点设到表外节点。"""
    ctx = FakeContext()
    ctx.recognition_map["主线_关卡列表"] = _ocr_result(["9-113"])

    result = MainStoryInitStage().analyze(ctx, _Arg(_init_param(stages=13)))

    assert ctx.anchors[ANCHOR] == "09_13"
    assert result is not None


def test_init_ignores_other_chapters_labels():
    ctx = FakeContext()
    ctx.recognition_map["主线_关卡列表"] = _ocr_result(["10-9", "9-3"])

    MainStoryInitStage().analyze(ctx, _Arg(_init_param()))

    assert ctx.anchors[ANCHOR] == "09_03"


# ------------------------------------------------------------- advance

def test_advance_walks_forward():
    ctx = FakeContext()
    ctx.anchors[ANCHOR] = "09_07"

    MainStoryAdvance().run(ctx, _Arg(_advance_param()))

    assert ctx.anchors[ANCHOR] == "09_08"


def test_advance_exits_chapter_after_last_stage():
    ctx = FakeContext()
    ctx.anchors[ANCHOR] = "09_13"

    MainStoryAdvance().run(ctx, _Arg(_advance_param()))

    assert ctx.anchors[ANCHOR] == "退出本章_09"


def test_advance_is_noop_without_anchor():
    """锚点没初始化时什么都不做，别把别的章的流程带跑。"""
    ctx = FakeContext()

    result = MainStoryAdvance().run(ctx, _Arg(_advance_param()))

    assert result.success is True
    assert ctx.anchors == {}


def test_advance_is_noop_for_foreign_target():
    ctx = FakeContext()
    ctx.anchors[ANCHOR] = "10_03"

    MainStoryAdvance().run(ctx, _Arg(_advance_param()))

    assert ctx.anchors[ANCHOR] == "10_03"


def test_advance_bad_param_does_not_raise():
    ctx = FakeContext()
    ctx.anchors[ANCHOR] = "09_02"

    MainStoryAdvance().run(ctx, _Arg({"anchor": ANCHOR, "chapter": "09", "stages": "x"}))

    assert ctx.anchors[ANCHOR] == "09_03"


# ------------------------------------------------------------ rollback

def test_rollback_steps_back_one_stage():
    ctx = FakeContext()
    ctx.anchors[ANCHOR] = "09_08"

    MainStoryRollback().run(ctx, _Arg(_rollback_param()))

    assert ctx.anchors[ANCHOR] == "09_07"


def test_rollback_gives_up_after_budget():
    """连着回退超过预算就收手，别在"打过-退回来"之间弹。"""
    ctx = FakeContext()
    ctx.anchors[ANCHOR] = "09_08"

    MainStoryRollback().run(ctx, _Arg(_rollback_param()))
    MainStoryRollback().run(ctx, _Arg(_rollback_param()))
    assert ctx.anchors[ANCHOR] == "09_06"

    MainStoryRollback().run(ctx, _Arg(_rollback_param()))
    assert ctx.anchors[ANCHOR] == "退出本章_09"


def test_rollback_gives_up_at_first_stage():
    ctx = FakeContext()
    ctx.anchors[ANCHOR] = "09_01"

    MainStoryRollback().run(ctx, _Arg(_rollback_param()))

    assert ctx.anchors[ANCHOR] == "退出本章_09"


def test_rollback_without_anchor_terminates():
    """没有锚点说明不是锚点流程，返回失败让链条结束，不要继续回退。"""
    ctx = FakeContext()

    result = MainStoryRollback().run(ctx, _Arg(_rollback_param()))

    assert result.success is False
    assert ctx.anchors == {}


def test_advance_resets_rollback_budget():
    ctx = FakeContext()
    ctx.anchors[ANCHOR] = "09_08"

    MainStoryRollback().run(ctx, _Arg(_rollback_param()))
    MainStoryRollback().run(ctx, _Arg(_rollback_param()))          # 预算用光
    MainStoryAdvance().run(ctx, _Arg(_advance_param()))            # 推进成功 → 预算清零

    assert ctx.anchors[ANCHOR] == "09_07"
    MainStoryRollback().run(ctx, _Arg(_rollback_param()))
    assert ctx.anchors[ANCHOR] == "09_06"


def test_legacy_tail_name_is_stable():
    """pipeline 里写死了这个收尾节点名，改名要同步改 Common.json。"""
    assert LEGACY_TAIL == "主线_旧流程结束"
