#!/usr/bin/env python3
"""Generate Auto_Main_Story chapter JSON (ER00-style, no hidden story)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "resource/base/pipeline/Auto_Main_Story/Chapters"

STORY_NEXT = [
    "[JumpBack]播放剧情",
    "[JumpBack]主线跳过",
    "跳过剧情",
]

CLICK_OFFSET = [30, 60, -30, 0]
SWIPE = {"begin": [900, 200], "end": [200, 200]}
POST_FREEZE = {
    "time": 500,
    "timeout": 2000,
    "target": [0, 0, 1280, 720],
}
CHAPTER_ROI = [33, 93, 500, 120]

# (file_stem_without_json, total_levels, extra_specials)
# extra_specials: list of (node_suffix, ocr_label, use_story_next)
# ER13: ER13-0 regular battle, ER13-17 story finale
CONFIG: list[tuple[str, int, list[tuple[str, str, bool]] | None]] = [
    ("ER02_枯朽为灯", 24, None),
    ("20_烬海异途", 14, None),
    ("ER03_未语庭言", 13, None),
    ("22_创绘映想", 28, None),
    ("23_凛桎鸣渊", 17, None),
    ("ER04_浮英枕梦行", 17, None),
    ("24_萦森歧路", 16, None),
    ("ER05_怒逐沉沙", 18, None),
    ("25_爝火长明", 21, None),
    ("26_摇篮游行", 27, None),
    ("27_碑火铸脊", 29, None),
    ("28_络勾陈", 38, None),
    ("29_源解信标", 18, None),
    ("30_镜像星尘", 17, None),
    ("ER06_幽塔黎光", 22, None),
    ("ER07_云梁觅影", 17, None),
    ("ER08_暮往长离", 26, None),
    ("ER09_晨昏庭影", 19, None),
    ("32_遥行循星", 25, None),
    ("33_锈夜逐光", 33, None),
    ("ER10_醉狱谲笼", 21, None),
    ("34_梦赴光寥之乡", 18, None),
    ("ER11_逐生复始", 16, None),
    ("ER12_末路燎原", 26, None),
    ("35_覆海离声", 22, None),
    ("36_溯梦归途", 14, None),
    (
        "ER13_织奏序言",
        17,
        [("_17", "ER13-17", True), ("_0", "ER13-0", False)],
    ),
    ("ER14_理想笼", 14, None),
    ("37_眠于厄寐之境", 26, None),
    ("38_推想视限", 21, None),
    ("39_冬冕的凋亡", 24, None),
    ("40_更美好的明天", 23, None),
    ("ER15_烈日将烬", 25, None),
    ("41_长路归航", 28, None),
]


def parse_stem(stem: str) -> tuple[str, str, str]:
    """Return (chapter_key, level_prefix, ocr_expected)."""
    if stem.startswith("ER"):
        er_id, title = stem.split("_", 1)
        return stem, er_id, f"{er_id}\\\\s*{title}"
    num, title = stem.split("_", 1)
    return stem, num, f"{num}\\\\s*{title}"


def level_labels(prefix: str, total: int) -> tuple[str, list[str]]:
    final = f"{prefix}-{total}"
    listing = [f"{prefix}-{i}" for i in range(total - 1, 0, -1)]
    return final, listing


def build_chapter(
    stem: str,
    total: int,
    extras: list[tuple[str, str, bool]] | None,
) -> dict:
    chapter_key, prefix, ocr_expected = parse_stem(stem)
    suffix = prefix  # ER02 or 20
    final_label, listing = level_labels(prefix, total)

    if extras:
        # Main list excludes final level and any extra OCR labels handled separately
        extra_labels = {e[1] for e in extras}
        listing = [x for x in listing if x not in extra_labels]
        if final_label not in extra_labels:
            pass  # final handled by extra node
        else:
            final_label = extras[-1][1]  # 剧情通关 uses last story special

    pick_main = f"选择最新关卡_{suffix}"
    clear_suffix = suffix.replace("-", "")

    next_entries: list[str] = []
    if extras:
        for node_suf, ocr, _ in extras:
            next_entries.append(f"[JumpBack]选择最新关卡_{suffix}{node_suf}")
        finale_for_clear = extras[-1][1]
    else:
        fin_node = f"选择最新关卡_{suffix}_{total}"
        next_entries.append(f"[JumpBack]{fin_node}")
        finale_for_clear = final_label

    next_entries.append(f"剧情通关_{clear_suffix}")
    next_entries.append(f"[JumpBack]{pick_main}")

    doc: dict = {
        chapter_key: {
            "recognition": {
                "type": "OCR",
                "param": {
                    "roi": CHAPTER_ROI,
                    "expected": ocr_expected,
                },
            },
            "action": {"type": "Swipe", "param": SWIPE},
            "post_wait_freezes": POST_FREEZE,
            "next": next_entries,
        },
        pick_main: {
            "recognition": {
                "type": "OCR",
                "param": {
                    "expected": listing,
                    "order_by": "Expected",
                },
            },
            "action": {
                "type": "Click",
                "param": {"target_offset": CLICK_OFFSET},
            },
            "next": ["主线_选关后战斗"],
        },
    }

    if extras:
        for node_suf, ocr, story in extras:
            node_name = f"选择最新关卡_{suffix}{node_suf}"
            doc[node_name] = {
                "max_hit": 1,
                "recognition": {
                    "type": "OCR",
                    "param": {"expected": [ocr]},
                },
                "action": {
                    "type": "Click",
                    "param": {"target_offset": CLICK_OFFSET},
                },
                "next": STORY_NEXT if story else ["主线_选关后战斗"],
            }
        clear_key = f"剧情通关_{clear_suffix}"
        doc[clear_key] = {
            "recognition": {
                "type": "OCR",
                "param": {"expected": [finale_for_clear]},
            },
            "next": ["返回"],
        }
    else:
        fin_node = f"选择最新关卡_{suffix}_{total}"
        doc[fin_node] = {
            "max_hit": 1,
            "recognition": {
                "type": "OCR",
                "param": {"expected": [final_label]},
            },
            "action": {
                "type": "Click",
                "param": {"target_offset": CLICK_OFFSET},
            },
            "next": STORY_NEXT,
        }
        doc[f"剧情通关_{clear_suffix}"] = {
            "recognition": {
                "type": "OCR",
                "param": {"expected": [final_label]},
            },
            "next": ["返回"],
        }

    return doc


def main() -> None:
    for stem, total, extras in CONFIG:
        path = OUT / f"{stem}.json"
        data = build_chapter(stem, total, extras)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=4) + "\n",
            encoding="utf-8",
        )
        print("wrote", path.name)


if __name__ == "__main__":
    main()
