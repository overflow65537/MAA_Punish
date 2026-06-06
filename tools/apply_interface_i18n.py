# -*- coding: utf-8 -*-
"""
将 interface.json、tasks/*.json 及 pipeline focus 文案迁移为 MaaEnd 风格 i18n。

- interface.json 增加 languages 映射
- 可翻译字段改为 $key 引用
- 生成 assets/locales/interface/zh_cn.json、zh_tw.json

用法:
  python tools/apply_interface_i18n.py          # dry-run
  python tools/apply_interface_i18n.py --write  # 写入文件
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    import opencc
except ImportError as exc:
    raise SystemExit(
        "需要安装 opencc-python-reimplemented: pip install opencc-python-reimplemented"
    ) from exc

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
INTERFACE_PATH = ASSETS / "interface.json"
TASKS_DIR = ASSETS / "tasks"
LOCALES_DIR = ASSETS / "locales" / "interface"
PIPELINE_DIRS = [
    ASSETS / "resource" / "base" / "pipeline",
    ASSETS / "resource" / "pgr_win32" / "pipeline",
    ASSETS / "resource" / "playcover" / "pipeline",
]

I18N_FIELD = re.compile(r"^\$[A-Za-z0-9_.\u4e00-\u9fff\-]+$")
HAS_CJK = re.compile(r"[\u4e00-\u9fff]")
SKIP_CASE_NAMES = frozenset({"Yes", "No", "CN", "EN"})

# OpenCC 对游戏专名/已有人工繁体对照的覆盖（简体 -> 繁体）
TW_OVERRIDES: dict[str, str] = {
    "战双帕弥什": "戰雙帕彌什",
    "帕弥什": "帕彌什",
    "囚笼": "囚籠",
    "幻痛囚笼": "幻痛囚籠",
    "肉鸽": "肉鴿",
    "矩阵": "矩陣",
    "宣叙妄响": "宣敘妄響",
    "厄愿潮声": "厄願潮聲",
    "矩阵循生": "矩陣循生",
    "寒境曙光": "寒境曙光",
    "神寂启示录": "神寂啟示錄",
    "雾夜镇魂曲": "霧夜鎮魂曲",
    "历战映射": "歷戰映射",
    "纷争战区": "紛爭戰區",
    "诺曼复兴战": "諾曼復興戰",
    "拟真围剿": "擬真圍剿",
    "拟战场域": "擬戰場域",
    "维系者行动": "維繫者行動",
    "链合回路": "鏈合回路",
    "洗词缀": "洗詞綴",
    "逆元碎片": "逆元碎片",
    "宿舍币": "宿舍幣",
    "遣测": "遣測",
    "终级": "終級",
    "终极区": "終極區",
    "终极": "終極",
    "BOSS": "BOSS",
    "QTE": "QTE",
    "MAS": "MAS",
    "Win32": "Win32",
    "PlayCover": "PlayCover",
    "Macos": "macOS",
    "PGR.exe": "PGR.exe",
    "launcher.exe": "launcher.exe",
}


class LocaleStore:
    def __init__(self, existing: dict[str, str] | None = None) -> None:
        self.zh_cn: dict[str, str] = dict(existing or {})
        self.s2t = opencc.OpenCC("s2t")

    def add(self, key: str, text: str) -> str:
        if not text or not isinstance(text, str):
            return text
        if I18N_FIELD.match(text):
            return text
        if key in self.zh_cn and self.zh_cn[key] != text:
            raise ValueError(f"key 冲突: {key!r}\n  已有: {self.zh_cn[key]!r}\n  新的: {text!r}")
        self.zh_cn[key] = text
        return f"${key}"

    def to_tw(self, text: str) -> str:
        result = text
        for cn, tw in sorted(TW_OVERRIDES.items(), key=lambda x: -len(x[0])):
            result = result.replace(cn, tw)
        return self.s2t.convert(result)

    def build_zh_tw(self) -> dict[str, str]:
        return {k: self.to_tw(v) for k, v in sorted(self.zh_cn.items())}


def should_i18n_string(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if I18N_FIELD.match(value):
        return False
    if value.startswith("./") or value.startswith("http"):
        return False
    if value.endswith(".md") or value.endswith(".png"):
        return False
    return bool(HAS_CJK.search(value) or "<" in value)


def i18n_option_fields(store: LocaleStore, opt_name: str, obj: dict[str, Any]) -> None:
    prefix = f"option.{opt_name}"
    if "label" not in obj or should_i18n_string(obj.get("label", "")):
        label = obj.get("label") or opt_name
        if should_i18n_string(label):
            obj["label"] = store.add(f"{prefix}.label", label)
    if "description" in obj and should_i18n_string(obj["description"]):
        obj["description"] = store.add(f"{prefix}.description", obj["description"])

    for case in obj.get("cases", []):
        if not isinstance(case, dict):
            continue
        case_name = case.get("name", "")
        case_prefix = f"{prefix}.cases.{case_name}"
        if case_name and case_name not in SKIP_CASE_NAMES and HAS_CJK.search(case_name):
            case["label"] = store.add(f"{case_prefix}.label", case_name)
        if "description" in case and should_i18n_string(case["description"]):
            case["description"] = store.add(f"{case_prefix}.description", case["description"])

    for inp in obj.get("inputs", []):
        if not isinstance(inp, dict):
            continue
        inp_name = inp.get("name", "")
        inp_prefix = f"{prefix}.inputs.{inp_name}"
        if "label" in inp and should_i18n_string(inp["label"]):
            inp["label"] = store.add(f"{inp_prefix}.label", inp["label"])
        elif inp_name and HAS_CJK.search(inp_name):
            inp["label"] = store.add(f"{inp_prefix}.label", inp_name)
        if "description" in inp and should_i18n_string(inp["description"]):
            inp["description"] = store.add(f"{inp_prefix}.description", inp["description"])
        if "pattern_msg" in inp and should_i18n_string(inp["pattern_msg"]):
            inp["pattern_msg"] = store.add(f"{inp_prefix}.pattern_msg", inp["pattern_msg"])


def i18n_task_block(store: LocaleStore, task: dict[str, Any]) -> None:
    name = task.get("name", "")
    if not name:
        return
    prefix = f"task.{name}"
    if "label" not in task or should_i18n_string(task.get("label", "")):
        task["label"] = store.add(f"{prefix}.label", name)
    if "description" in task and should_i18n_string(task["description"]):
        task["description"] = store.add(f"{prefix}.description", task["description"])


def i18n_interface(store: LocaleStore, data: dict[str, Any]) -> None:
    if should_i18n_string(data.get("name", "")):
        data["name"] = store.add("project.name", data["name"])
    if should_i18n_string(data.get("description", "")):
        data["description"] = store.add("project.description", data["description"])

    for ctrl in data.get("controller", []):
        cname = ctrl.get("name", "")
        cp = f"controller.{cname}"
        display = ctrl.get("label") or cname
        if should_i18n_string(display):
            ctrl["label"] = store.add(f"{cp}.label", display)
        if "description" in ctrl and should_i18n_string(ctrl["description"]):
            ctrl["description"] = store.add(f"{cp}.description", ctrl["description"])

    for res in data.get("resource", []):
        rname = res.get("name", "")
        if rname and HAS_CJK.search(rname):
            res["label"] = store.add(f"resource.{rname}.label", rname)

    for grp in data.get("group", []):
        gname = grp.get("name", "")
        gp = f"group.{gname}"
        if "label" in grp and should_i18n_string(grp["label"]):
            grp["label"] = store.add(f"{gp}.label", grp["label"])
        if "description" in grp and should_i18n_string(grp["description"]):
            grp["description"] = store.add(f"{gp}.description", grp["description"])

    for preset in data.get("preset", []):
        pname = preset.get("name", "")
        pp = f"preset.{pname}"
        if "label" in preset and should_i18n_string(preset["label"]):
            preset["label"] = store.add(f"{pp}.label", preset["label"])
        if "description" in preset and should_i18n_string(preset.get("description", "")):
            preset["description"] = store.add(f"{pp}.description", preset["description"])

    for opt_name, opt_def in data.get("option", {}).items():
        if isinstance(opt_def, dict):
            i18n_option_fields(store, opt_name, opt_def)


def i18n_task_file(store: LocaleStore, data: dict[str, Any]) -> None:
    for task in data.get("task", []):
        if isinstance(task, dict):
            i18n_task_block(store, task)
    for opt_name, opt_def in data.get("option", {}).items():
        if isinstance(opt_def, dict):
            i18n_option_fields(store, opt_name, opt_def)


NODE_LINE_RE = re.compile(r'^(\s*)"([^"]+)":\s*\{\s*(?://.*)?$')
FOCUS_LINE_RE = re.compile(r'^(\s*)"focus":\s*\{\s*(?://.*)?$')
FOCUS_EVENT_LINE_RE = re.compile(
    r'^(\s*)"(Node\.[^"]+)":\s*"((?:\\.|[^"\\])*)"\s*,?\s*(?://.*)?$'
)
CLOSE_BRACE_RE = re.compile(r'^(\s*)\}\s*,?\s*(?://.*)?$')


def i18n_pipeline_focus(store: LocaleStore, pipeline_dir: Path) -> list[tuple[Path, str, str]]:
    """按行解析 jsonc，替换 focus 内 Node.* 文案。返回 [(path, old, new), ...]"""
    changes: list[tuple[Path, str, str]] = []
    for path in sorted(pipeline_dir.rglob("*")):
        if path.suffix not in {".json", ".jsonc"}:
            continue
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(pipeline_dir)
        file_stem = (
            str(rel)
            .replace("\\", "/")
            .replace("/", ".")
            .removesuffix(".jsonc")
            .removesuffix(".json")
        )
        pack = pipeline_dir.relative_to(ASSETS / "resource").parts[0]
        stem = f"{pack}.{file_stem}"

        lines = text.splitlines(keepends=True)
        new_lines: list[str] = []
        current_node: str | None = None
        in_focus = False
        focus_indent = 0
        changed = False

        for line in lines:
            node_m = NODE_LINE_RE.match(line.rstrip("\n"))
            if node_m and not in_focus and node_m.group(2) != "focus":
                # 仅跟踪 pipeline 顶层节点（4 空格缩进），避免误认嵌套字段
                if len(node_m.group(1)) == 4:
                    current_node = node_m.group(2)

            focus_m = FOCUS_LINE_RE.match(line.rstrip("\n"))
            if focus_m:
                in_focus = True
                focus_indent = len(focus_m.group(1))
                new_lines.append(line)
                continue

            if in_focus:
                event_m = FOCUS_EVENT_LINE_RE.match(line.rstrip("\n"))
                if event_m:
                    event_key = event_m.group(2)
                    raw_value = json.loads(f'"{event_m.group(3)}"')
                    if should_i18n_string(raw_value) and current_node:
                        safe_node = current_node.replace(".", "_")
                        i18n_key = f"focus.{stem}.{safe_node}.{event_key}"
                        translated = store.add(i18n_key, raw_value)
                        indent = event_m.group(1)
                        trail = "," if "," in line.rstrip("\n") else ""
                        comment = ""
                        if "//" in line:
                            comment = " " + line.split("//", 1)[1].rstrip("\n")
                            if not comment.startswith(" "):
                                comment = " " + comment.lstrip()
                        new_lines.append(
                            f'{indent}"{event_key}": "{translated}"{trail}{comment}\n'
                        )
                        changed = True
                        continue

                close_m = CLOSE_BRACE_RE.match(line.rstrip("\n"))
                if close_m and len(close_m.group(1)) == focus_indent:
                    in_focus = False

            new_lines.append(line)

        new_text = "".join(new_lines)
        if changed:
            changes.append((path, text, new_text))
    return changes


def dump_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="迁移 interface i18n")
    parser.add_argument("--write", action="store_true", help="写入文件（默认仅统计）")
    parser.add_argument("--skip-pipeline", action="store_true", help="跳过 pipeline focus")
    args = parser.parse_args()

    existing_locale: dict[str, str] = {}
    zh_cn_path = LOCALES_DIR / "zh_cn.json"
    if zh_cn_path.is_file():
        with open(zh_cn_path, encoding="utf-8") as f:
            existing_locale = json.load(f)
    store = LocaleStore(existing_locale)

    with open(INTERFACE_PATH, encoding="utf-8") as f:
        interface = json.load(f)

    i18n_interface(store, interface)
    interface["languages"] = {
        "zh_cn": "locales/interface/zh_cn.json",
        "zh_tw": "locales/interface/zh_tw.json",
    }

    task_files: list[Path] = []
    for path in sorted(TASKS_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            task_data = json.load(f)
        i18n_task_file(store, task_data)
        task_files.append(path)
        if args.write:
            dump_json(path, task_data)

    pipeline_changes: list[tuple[Path, str, str]] = []
    if not args.skip_pipeline:
        for pdir in PIPELINE_DIRS:
            if pdir.is_dir():
                pipeline_changes.extend(i18n_pipeline_focus(store, pdir))

    zh_tw = store.build_zh_tw()

    print(f"zh_cn keys: {len(store.zh_cn)}")
    print(f"zh_tw keys: {len(zh_tw)}")
    print(f"task files: {len(task_files)}")
    print(f"pipeline files to update: {len(pipeline_changes)}")

    if args.write:
        dump_json(INTERFACE_PATH, interface)
        dump_json(LOCALES_DIR / "zh_cn.json", store.zh_cn)
        dump_json(LOCALES_DIR / "zh_tw.json", zh_tw)
        for path, _old, new in pipeline_changes:
            path.write_text(new, encoding="utf-8", newline="\n")
        print("已写入 interface、locales 与 pipeline focus。")
    else:
        print("dry-run 完成，使用 --write 写入。")


if __name__ == "__main__":
    main()
