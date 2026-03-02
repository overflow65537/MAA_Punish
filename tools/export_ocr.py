# -*- coding: utf-8 -*-
"""
遍历 assets/resource/base/pipeline 下所有 json/jsonc 文件，
提取 OCR 相关节点的中文 expected，导出为 OCR_i18n.json。
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_PIPELINE_BASE = ROOT_DIR / "assets" / "resource" / "base" / "pipeline"
OUTPUT_PATH = ROOT_DIR /"assets"/ "misc" / "OCR_i18n.json"


def strip_jsonc_comments(text: str) -> str:
    """从 apply_ocr_i18n.py 复制的 JSONC 行/块注释去除逻辑。"""
    lines = []
    in_block = False
    for line in text.split("\n"):
        s = line.strip()
        if in_block:
            if "*/" in line:
                in_block = False
                idx = line.find("*/") + 2
                rest = line[idx:].strip()
                if rest:
                    lines.append(" " * (len(line) - len(line.lstrip())) + rest)
            continue
        if "/*" in line and "*/" not in line:
            in_block = True
            before = line[: line.find("/*")].strip()
            if before and not before.startswith("//"):
                lines.append(line[: line.find("/*")].rstrip())
            continue
        if s.startswith("//"):
            continue
        if "//" in line:
            in_string = False
            escape = False
            quote: Optional[str] = None
            new_line = []
            i = 0
            while i < len(line):
                c = line[i]
                if escape:
                    new_line.append(c)
                    escape = False
                    i += 1
                    continue
                if c == "\\" and in_string:
                    escape = True
                    new_line.append(c)
                    i += 1
                    continue
                if c in '"\'' and not escape:
                    if not in_string:
                        in_string = True
                        quote = c
                    elif c == quote:
                        in_string = False
                    new_line.append(c)
                    i += 1
                    continue
                if not in_string and c == "/" and i + 1 < len(line) and line[i + 1] == "/":
                    line = "".join(new_line) + "\n"
                    break
                new_line.append(c)
                i += 1
            else:
                line = "".join(new_line)
        lines.append(line)
    return "\n".join(lines)


def load_json_or_jsonc(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(strip_jsonc_comments(text))


def pick_zh_from_expected(value: Any) -> str:
    """
    将 expected 的值规整为 zh_CN：
    - str：直接返回
    - list：返回第一个字符串元素（通常是简中原文）
    - 其他：转成字符串
    """
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                return item
        return str(value)
    return str(value)


def extract_ocr_info(node_name: str, node: Any, rel_path: str) -> Optional[Dict[str, str]]:
    """
    从单个节点中提取 OCR 对应的 expected：
    - recognition.type == "OCR"
    - 或 recognition == "OCR"
    - expected 优先从 recognition.param.expected / recognition.expected，其次 action.expected
    """
    if not isinstance(node, dict):
        return None

    is_ocr = False
    rec = node.get("recognition")
    rec_expected = None

    if isinstance(rec, dict):
        if rec.get("type") == "OCR":
            is_ocr = True
            param = rec.get("param", {})
            if isinstance(param, dict) and "expected" in param:
                rec_expected = param.get("expected")
            elif "expected" in rec:
                rec_expected = rec.get("expected")
    elif isinstance(rec, str) and rec == "OCR":
        is_ocr = True

    # 兼容极简结构：节点自身就是 OCR
    if not is_ocr and node.get("type") == "OCR":
        is_ocr = True
        if "expected" in node:
            rec_expected = node.get("expected")

    action_expected = None
    action = node.get("action")
    if isinstance(action, dict) and "expected" in action:
        action_expected = action.get("expected")

    if not is_ocr:
        return None

    expected_value = rec_expected if rec_expected is not None else action_expected
    if expected_value is None:
        return None

    zh_cn = pick_zh_from_expected(expected_value)
    return {
        "path": rel_path,
        "zh_CN": zh_cn,
    }


def main() -> None:
    if not ASSETS_PIPELINE_BASE.exists():
        raise SystemExit(f"未找到目录: {ASSETS_PIPELINE_BASE}")

    result: Dict[str, Dict[str, str]] = {}

    for path in sorted(ASSETS_PIPELINE_BASE.rglob("*.json*")):
        data = load_json_or_jsonc(path)
        if not isinstance(data, dict):
            continue
        rel_path = str(path.relative_to(ROOT_DIR)).replace("\\", "/")

        for node_name, node in data.items():
            info = extract_ocr_info(node_name, node, rel_path)
            if info is not None:
                # 若不同文件中有同名节点，后者会覆盖前者
                result[node_name] = info

    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=4),
        encoding="utf-8",
    )
    print(f"已写出 {len(result)} 条 OCR 记录到 {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

