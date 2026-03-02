# -*- coding: utf-8 -*-
"""
根据 assets/misc/OCR_i18n.json 生成各语言的 OCR 资源文件。

规则：
- OCR_i18n.json 中每个键为节点名，值中包含：
  - path: 原始简中流水线文件路径（通常在 assets/resource/base/pipeline 下）
  - zh_CN: 简体中文文本
  - 其他键（如 zh_TW、en_US 等）：目标语言文本
- 对于每个目标语言 lang（例如 zh_TW）：
  - 将 path 中的 "/base/" 替换成 f"/{lang}/"
  - 在对应路径创建（或覆盖）一个仅包含 OCR 节点的 json/jsonc 文件：
    {
        "节点名": {
            "expected": "对应语言的文本"
        },
        ...
    }
"""

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, DefaultDict, Dict, Iterable, Mapping, MutableMapping, Set


ROOT_DIR = Path(__file__).resolve().parent.parent
OCR_I18N_PATH = ROOT_DIR / "assets" / "misc" / "OCR_i18n.json"

# 在 OCR_i18n.json 中，这些键不是语言代码
NON_LANG_KEYS: Set[str] = {"path", "zh_CN"}


def load_ocr_i18n() -> Dict[str, Dict[str, Any]]:
    text = OCR_I18N_PATH.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise SystemExit(f"OCR_i18n.json 结构异常: 根节点不是对象: {type(data)!r}")
    return data


def detect_languages(data: Mapping[str, Mapping[str, Any]]) -> Set[str]:
    """
    自动从 OCR_i18n.json 中提取所有的语言代码键。
    例如：{"path", "zh_CN", "zh_TW", "en_US"} -> 返回 {"zh_TW", "en_US"}
    """
    langs: Set[str] = set()
    for info in data.values():
        if not isinstance(info, Mapping):
            continue
        for key in info.keys():
            if key in NON_LANG_KEYS:
                continue
            langs.add(key)
    return langs


def build_files_for_language(
    data: Mapping[str, Mapping[str, Any]],
    lang: str,
) -> DefaultDict[Path, Dict[str, Dict[str, Any]]]:
    """
    按文件分组，构建指定语言的节点映射：
    { 目标文件路径: { 节点名: {"expected": 文本} } }
    """
    result: DefaultDict[Path, Dict[str, Dict[str, Any]]] = defaultdict(dict)

    for node_name, info in data.items():
        if not isinstance(info, Mapping):
            continue

        rel_path = info.get("path")
        if not isinstance(rel_path, str):
            continue

        # 必须有该语言的翻译
        if lang not in info:
            continue

        # 只处理包含 "/base/" 的路径，避免误伤其他资源
        if "/base/" not in rel_path:
            continue

        target_rel = rel_path.replace("/base/", f"/{lang}/", 1)
        target_path = ROOT_DIR / target_rel

        text = info[lang]
        # 直接使用 OCR_i18n.json 中的值，不做额外处理
        result[target_path][node_name] = {"expected": text}

    return result


def write_language_files(
    file_map: Mapping[Path, Mapping[str, Mapping[str, Any]]],
) -> None:
    for path, nodes in file_map.items():
        if not nodes:
            continue

        path.parent.mkdir(parents=True, exist_ok=True)

        # 为了输出稳定性，按节点名排序
        ordered_nodes: MutableMapping[str, Mapping[str, Any]] = {
            name: nodes[name] for name in sorted(nodes.keys())
        }

        text = json.dumps(ordered_nodes, ensure_ascii=False, indent=4)
        path.write_text(text, encoding="utf-8")

        try:
            rel = path.relative_to(ROOT_DIR)
        except ValueError:
            rel = path
        print(f"写出 {len(ordered_nodes)} 个节点到 {rel}")


def parse_languages_from_argv(argv: Iterable[str], data: Mapping[str, Mapping[str, Any]]) -> Iterable[str]:
    args = list(argv)
    if not args:
        # 默认只生成繁中
        return ["zh_TW"]

    if args[0] in {"--all", "--all-langs"}:
        langs = sorted(detect_languages(data))
        if not langs:
            raise SystemExit("在 OCR_i18n.json 中未检测到任何语言键。")
        return langs

    # 其余情况将第一个参数视为语言代码
    return [args[0]]


def main(argv: Iterable[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    if not OCR_I18N_PATH.exists():
        raise SystemExit(f"未找到 OCR_i18n 文件: {OCR_I18N_PATH}")

    data = load_ocr_i18n()
    langs = list(parse_languages_from_argv(argv, data))

    print(f"将为以下语言生成 OCR 资源文件: {', '.join(langs)}")

    for lang in langs:
        print(f"\n=== 处理语言: {lang} ===")
        file_map = build_files_for_language(data, lang)
        if not file_map:
            print(f"  警告: 未找到任何包含语言键 {lang!r} 的节点，跳过。")
            continue
        write_language_files(file_map)


if __name__ == "__main__":
    main()

