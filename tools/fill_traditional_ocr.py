# -*- coding: utf-8 -*-
"""
为 base pipeline 中 OCR expected 里尚未配对的简体补充繁体。

优先级：marker 精确对照 > OCR_i18n.json > OpenCC s2t

规则：
- 跳过正则、纯英文、空字符串等
- 已有繁体配对（下一项即为对应繁体）则跳过
- 简繁相同（如角色名）不追加
- 已是繁体（OpenCC t2s 可还原为简体）且无简体配对时，不追加
- 就地 patch json/jsonc，保留注释
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple

try:
    import opencc
except ImportError as exc:
    raise SystemExit("需要安装 opencc-python-reimplemented: pip install opencc-python-reimplemented") from exc

from export_ocr import ASSETS_PIPELINE_BASE, ROOT_DIR

OCR_I18N_PATH = ROOT_DIR / "assets" / "misc" / "OCR_i18n.json"
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
REGEX_HINT_RE = re.compile(r"[\^\\.*+?|()\[\]{}$]")
SKIP_LITERALS: Set[str] = {"", "OFF", "SKIP"}


def load_marker_lookup(markers_path: Path) -> Dict[str, str]:
    raw = json.loads(markers_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise SystemExit(f"marker 文件结构异常: {type(raw)!r}")

    lookup: Dict[str, str] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        zh_cn = item.get("zh_cn")
        zh_tw = item.get("zh_tw")
        if isinstance(zh_cn, str) and isinstance(zh_tw, str) and zh_cn not in lookup:
            lookup[zh_cn] = zh_tw
    return lookup


def load_ocr_i18n_lookup() -> Dict[str, str]:
    if not OCR_I18N_PATH.exists():
        return {}
    data = json.loads(OCR_I18N_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}

    lookup: Dict[str, str] = {}
    for info in data.values():
        if not isinstance(info, dict):
            continue
        zh_cn = info.get("zh_CN")
        zh_tw = info.get("zh_TW")
        if isinstance(zh_cn, str) and isinstance(zh_tw, str) and zh_cn not in lookup:
            lookup[zh_cn] = zh_tw
    return lookup


def is_skippable_item(item: str) -> bool:
    if item in SKIP_LITERALS:
        return True
    if not CJK_RE.search(item):
        return True
    if REGEX_HINT_RE.search(item):
        return True
    return False


def _normalize_expected_items(expected: Any) -> List[str]:
    if isinstance(expected, str):
        return [expected]
    if isinstance(expected, list):
        return [item for item in expected if isinstance(item, str)]
    return [str(expected)]


def _compact_expected(items: List[str]) -> Any:
    if len(items) == 1:
        return items[0]
    return items


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


class TwResolver:
    def __init__(
        self,
        marker_lookup: Mapping[str, str],
        i18n_lookup: Mapping[str, str],
    ) -> None:
        self.marker_lookup = marker_lookup
        self.i18n_lookup = i18n_lookup
        self.s2t = opencc.OpenCC("s2t")
        self.t2s = opencc.OpenCC("t2s")

    def resolve(self, text: str) -> Optional[str]:
        if text in self.marker_lookup:
            tw = self.marker_lookup[text]
            return tw if tw != text else None

        if text in self.i18n_lookup:
            tw = self.i18n_lookup[text]
            return tw if tw != text else None

        converted = self.s2t.convert(text)
        if converted == text:
            return None

        # 已是繁体文本，不再追加
        if self.t2s.convert(text) != text:
            return None

        return converted


def expand_expected_with_traditional(
    expected: Any,
    resolver: TwResolver,
) -> Tuple[Any, bool]:
    items = _normalize_expected_items(expected)
    output: List[str] = []
    changed = False
    index = 0

    while index < len(items):
        item = items[index]
        output.append(item)

        if is_skippable_item(item):
            index += 1
            continue

        tw = resolver.resolve(item)
        if tw is not None and index + 1 < len(items) and items[index + 1] == tw:
            index += 1
            continue

        if tw is not None and tw not in items[index + 1 :]:
            output.append(tw)
            changed = True

        index += 1

    output = _dedupe_preserve_order(output)
    compacted = _compact_expected(output)
    if compacted == expected:
        return expected, False
    return compacted, True


def _skip_ws(text: str, index: int) -> int:
    while index < len(text) and text[index] in " \t\n\r":
        index += 1
    return index


def _find_json_value_end(text: str, start: int) -> int:
    start = _skip_ws(text, start)
    if start >= len(text):
        return start

    char = text[start]
    if char == '"':
        index = start + 1
        escape = False
        while index < len(text):
            if escape:
                escape = False
            elif text[index] == "\\":
                escape = True
            elif text[index] == '"':
                return index + 1
            index += 1
        return len(text)

    if char == "[":
        index = start + 1
        while index < len(text):
            index = _skip_ws(text, index)
            if index >= len(text):
                break
            if text[index] == "]":
                return index + 1
            index = _find_json_value_end(text, index)
            index = _skip_ws(text, index)
            if index < len(text) and text[index] == ",":
                index += 1
        return len(text)

    if char == "{":
        depth = 0
        index = start
        while index < len(text):
            if text[index] == '"':
                index = _find_json_value_end(text, index)
                continue
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    return index + 1
            index += 1
        return len(text)

    match = re.match(r"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null)", text[start:])
    if match:
        return start + match.end()
    return start + 1


def patch_all_expected_in_file(content: str, resolver: TwResolver) -> Tuple[str, int]:
    patched = 0
    search_from = 0

    while True:
        match = re.search(r'"expected"\s*:\s*', content[search_from:])
        if not match:
            break

        abs_start = search_from + match.end()
        abs_end = _find_json_value_end(content, abs_start)
        old_raw = content[abs_start:abs_end]
        try:
            old_val = json.loads(old_raw)
        except json.JSONDecodeError:
            search_from = abs_end
            continue

        new_val, changed = expand_expected_with_traditional(old_val, resolver)
        if changed:
            new_raw = json.dumps(new_val, ensure_ascii=False)
            content = content[:abs_start] + new_raw + content[abs_end:]
            patched += 1
            search_from = abs_start + len(new_raw)
        else:
            search_from = abs_end

    return content, patched


def apply_to_pipeline(
    resolver: TwResolver,
    *,
    dry_run: bool = False,
) -> int:
    if not ASSETS_PIPELINE_BASE.exists():
        raise SystemExit(f"未找到 pipeline 目录: {ASSETS_PIPELINE_BASE}")

    total_patched = 0
    files_touched = 0

    for path in sorted(ASSETS_PIPELINE_BASE.rglob("*.json*")):
        content = path.read_text(encoding="utf-8")
        new_content, file_patched = patch_all_expected_in_file(content, resolver)

        if file_patched == 0:
            continue

        files_touched += 1
        total_patched += file_patched
        rel = path.relative_to(ROOT_DIR)
        print(f"  {'[dry-run] ' if dry_run else ''}{rel}: {file_patched} 处 expected")

        if not dry_run:
            path.write_text(new_content, encoding="utf-8")

    print(f"共更新 {total_patched} 处 expected，涉及 {files_touched} 个文件")
    return total_patched


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="为 OCR expected 中未配对的简体补充繁体")
    parser.add_argument(
        "--markers",
        type=Path,
        required=True,
        help="PGR 简繁 marker JSON（zh_cn_tw_en.json）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅统计，不写回文件",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)
    marker_lookup = load_marker_lookup(args.markers)
    i18n_lookup = load_ocr_i18n_lookup()
    resolver = TwResolver(marker_lookup, i18n_lookup)

    print("=== 补充 OCR expected 繁体 ===")
    print(f"  marker: {len(marker_lookup)} 条")
    print(f"  OCR_i18n fallback: {len(i18n_lookup)} 条")
    print(f"  OpenCC: s2t")

    apply_to_pipeline(resolver, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
