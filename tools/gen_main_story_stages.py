#!/usr/bin/env python3
"""Generate anchor-based stage nodes for Auto_Main_Story chapters.

背景：原来的 `选择最新关卡_XX` 每帧都用 OCR 结果的几何顺序猜"该打第几关"，
选到哪一关取决于当前滚动位置和标签框的像素坐标，于是会出现 9/10 来回跳。
这里改成"一关一个节点 + 锚点推进"：

    进入章节 → 滑动到最新关卡
      → MainStoryInitStage 用一次 OCR 把锚点 `当前关卡` 设到当前这一关
      → `[Anchor]当前关卡` 跳到该关节点 → 点击 → 战斗
      → 回到章节界面 → `[Anchor]当前章节推进` → MainStoryAdvance 把锚点往前推一格

锚点只会往前推，OCR 只负责"把这一关的卡片找出来点下去"，不再负责"该打第几关"。

用法:
    python tools/gen_main_story_stages.py --check
    python tools/gen_main_story_stages.py --chapter 09_黑星坠落
    python tools/gen_main_story_stages.py --all
"""

from __future__ import annotations

import argparse
import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHAPTERS = ROOT / "resource/base/pipeline/Auto_Main_Story/Chapters"
TABLE = ROOT / "tools/main_story_stages.json"

# 关卡标签的点击偏移，沿用旧节点的值（标签右下方的卡片本体）
CLICK_OFFSET = [30, 60, -30, 0]


def load_table() -> list[dict]:
    data = json.loads(TABLE.read_text(encoding="utf-8"))
    return data["chapters"]


def stage_label_regex(prefix: str, stage: int) -> str:
    """精确匹配 `9-13` 这样的关卡标签。

    OCR 的 expected 是正则搜索，裸写 `9-1` 会命中 `9-13`，
    所以这里锚定开头并用负向先行断言挡掉更长的关号。
    """
    return f"^{prefix}-{stage}(?!\\d)"


def build(chapter: dict, entry: dict, local_nodes: set[str]) -> dict:
    key = chapter["key"]
    num = chapter["chapter"]          # 节点名前缀，如 09 / ER02
    prefix = chapter["label_prefix"]  # 关卡标签前缀，如 9 / ER02
    stages = int(chapter["stages"])

    # 入口节点：识别/动作/等待全部保留，只重写 next。
    # 保留那些指向"非本文件节点"的引用（例如 09/15/16 的隐藏剧情分支）。
    head = copy.deepcopy(entry)
    kept = [
        ref for ref in (head.get("next") or [])
        if strip_attr(ref) not in local_nodes
    ]
    head["next"] = kept + [f"初始化关卡_{num}"]

    doc: dict = {key: head}

    doc[f"初始化关卡_{num}"] = {
        "recognition": {
            "type": "Custom",
            "param": {
                "custom_recognition": "MainStoryInitStage",
                "custom_recognition_param": {
                    "chapter": num,
                    "label_prefix": prefix,
                    "stages": stages,
                },
            },
        },
        "action": {"type": "DoNothing"},
        "next": ["主线_打当前关"],
    }

    for i in range(1, stages + 1):
        doc[f"{num}_{i:02d}"] = {
            "recognition": {
                "type": "OCR",
                "param": {"expected": stage_label_regex(prefix, i)},
            },
            "action": {"type": "Click", "param": {"target_offset": CLICK_OFFSET}},
            "next": ["主线_选关后战斗"],
        }

    doc[f"推进关卡_{num}"] = {
        "recognition": {"type": "DirectHit"},
        "action": {
            "type": "Custom",
            "param": {
                "custom_action": "MainStoryAdvance",
                "custom_action_param": {
                    "chapter": num,
                    "label_prefix": prefix,
                    "stages": stages,
                },
            },
        },
        "next": ["主线_打当前关"],
    }

    doc[f"退出本章_{num}"] = {
        "recognition": {"type": "DirectHit"},
        "action": {"type": "DoNothing"},
        # 清锚点：否则任务切到未接入锚点的章节后，残留的 `当前章节推进`
        # 会在那边的"回到章节界面"被重新解析，把流程拖回本章的节点。
        "anchor": {"当前关卡": "", "当前章节推进": ""},
        "next": ["返回"],
    }

    return doc


def strip_attr(ref) -> str:
    """去掉 next 里的 `[JumpBack]` / `[Anchor]` 前缀，拿到节点名。"""
    if isinstance(ref, dict):
        return ref.get("name", "")
    return ref.split("]", 1)[-1] if ref.startswith("[") else ref


def generate(chapter: dict, write: bool) -> str:
    path = CHAPTERS / f"{chapter['key']}.json"
    old = json.loads(path.read_text(encoding="utf-8"))
    entry_name = next(iter(old))
    entry = old[entry_name]
    local_nodes = set(old) - {entry_name}
    doc = build(chapter, entry, local_nodes)
    text = json.dumps(doc, ensure_ascii=False, indent=4) + "\n"
    if write:
        path.write_text(text, encoding="utf-8")
        return f"wrote {path.name} ({len(doc)} nodes)"
    if path.read_text(encoding="utf-8") != text:
        return f"DIFF {path.name}"
    return f"ok   {path.name}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="转换表里所有 mode=anchor 的章节")
    ap.add_argument("--chapter", action="append", default=[], help="只转换指定章节（文件名去 .json）")
    ap.add_argument("--check", action="store_true", help="只检查文件是否与生成结果一致，不写盘")
    args = ap.parse_args()

    table = load_table()
    wanted = set(args.chapter)
    todo = []
    for ch in table:
        if ch.get("mode") != "anchor":
            continue
        if wanted and ch["key"] not in wanted:
            continue
        todo.append(ch)
    if wanted - {c["key"] for c in todo}:
        missing = sorted(wanted - {c["key"] for c in todo})
        print(f"unknown or non-anchor chapter: {missing}", file=sys.stderr)
        return 2

    write = not args.check
    diffs = 0
    for ch in todo:
        msg = generate(ch, write)
        print(msg)
        if msg.startswith("DIFF"):
            diffs += 1
    return 1 if diffs else 0


if __name__ == "__main__":
    raise SystemExit(main())
