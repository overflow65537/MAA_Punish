# -*- coding: utf-8 -*-
"""
将 ocr_i18n.json 中的繁体中文翻译应用到 assets/resource 下的资源文件。
- 若资源中 expected 为 str：改为 [原值, ...翻译]
- 若资源中 expected 为 list：仅将翻译追加到列表中（不重复）
"""
import json
from pathlib import Path
from collections import defaultdict

ASSETS_BASE = Path(__file__).resolve().parent / "assets" / "resource" / "base"
OCR_I18N_PATH = Path(__file__).resolve().parent / "ocr_i18n.json"


def strip_jsonc_comments(text: str) -> str:
    """简单移除 JSONC 的 // 行注释，便于解析。"""
    lines = []
    in_block = False
    for line in text.split("\n"):
        s = line.strip()
        if in_block:
            if "*/" in line:
                in_block = False
                # 保留 */ 之后的内容
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
        # 去掉行内 // 注释（简单处理：仅当 // 在字符串外时）
        if "//" in line:
            in_string = False
            escape = False
            quote = None
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
                    # 行尾注释，截断
                    line = "".join(new_line) + "\n"
                    break
                new_line.append(c)
                i += 1
            else:
                line = "".join(new_line)
        lines.append(line)
    return "\n".join(lines)


def load_json_or_jsonc(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(strip_jsonc_comments(text))


def collect_ocr_units(obj):
    """
    收集顶层 task 中 recognition.type == "OCR" 且 param 中有 expected 的节点。
    按 JSON 中 key 的顺序，与 ocr_i18n 的 index 对应。
    返回 [param, ...]，param 为可直接修改的引用。
    """
    results = []
    for _key, node in obj.items():
        if not isinstance(node, dict):
            continue
        rec = node.get("recognition", {})
        if rec.get("type") != "OCR":
            continue
        param = rec.get("param", {})
        if "expected" not in param:
            continue
        results.append(param)
    return results


def main():
    # ocr_i18n.json 可能为 UTF-8 或 UTF-16
    raw = OCR_I18N_PATH.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        i18n = json.loads(raw.decode("utf-16"))
    else:
        i18n = json.loads(raw.decode("utf-8-sig"))
    entries = i18n.get("entries", [])

    # 按文件分组
    by_file = defaultdict(list)
    for e in entries:
        rel = e["file"].replace("\\", "/")
        full_path = ASSETS_BASE / rel
        if not full_path.exists():
            print(f"跳过不存在的文件: {full_path}")
            continue
        by_file[full_path].append(e)

    for file_path, file_entries in sorted(by_file.items(), key=lambda x: str(x[0])):
        data = load_json_or_jsonc(file_path)
        ocr_units = collect_ocr_units(data)

        # 按 index 排序，确保按顺序应用
        for e in sorted(file_entries, key=lambda x: x["index"]):
            idx = e["index"]
            if idx >= len(ocr_units):
                print(f"警告: {file_path} index={idx} 超出 OCR 单元数量 {len(ocr_units)}")
                continue
            param = ocr_units[idx]
            current = param.get("expected")
            translation = e.get("expected")

            if translation is None:
                continue

            trans_list = translation if isinstance(translation, list) else [translation]

            if isinstance(current, str):
                # 原为 str：改为 [原值, ...翻译]，始终追加 i18n 的 expected
                new_expected = [current] + trans_list
            else:
                # 原为 list：追加 i18n 的 expected（若简繁同形则也追加以保持 [原, 繁] 两项）
                current_list = current if isinstance(current, list) else [current]
                existing = set(current_list)
                if len(current_list) == 1 and len(trans_list) == 1 and current_list[0] == trans_list[0]:
                    added = trans_list  # 简繁同形时仍追加，保持 [原, 繁] 结构
                else:
                    added = [t for t in trans_list if t not in existing]
                new_expected = current_list + added

            param["expected"] = new_expected

        # 写回文件，保持 4 空格缩进、不转义中文
        file_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )
        print(f"已更新: {file_path.relative_to(Path(__file__).resolve().parent)}")


if __name__ == "__main__":
    main()
