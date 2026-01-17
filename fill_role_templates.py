# -*- coding: utf-8 -*-
"""
自动将人物索引中的模板路径写回 LoadSetting.py 的 ROLE_ACTIONS.template
用法: python fill_role_templates.py
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
LOADSETTING_PATH = (
    PROJECT_ROOT / "assets" / "MPAcustom" / "action" / "tool" / "LoadSetting.py"
)
TEMPLATE_ROOT = (
    PROJECT_ROOT / "assets" / "resource" / "base" / "image" / "人物索引"
)


def _collect_templates(role_key: str) -> list[str] | None:
    if "·" not in role_key:
        return None
    character_name, role_name = role_key.split("·", 1)
    role_dir = TEMPLATE_ROOT / character_name / role_name
    if not role_dir.is_dir():
        return None
    png_files = sorted(role_dir.rglob("*.png"))
    if not png_files:
        return None
    rel_root = TEMPLATE_ROOT.parent
    return [str(path.relative_to(rel_root)).replace("\\", "/") for path in png_files]


def _update_loadsetting() -> int:
    lines = LOADSETTING_PATH.read_text(encoding="utf-8").splitlines(keepends=True)
    output: list[str] = []
    current_role: str | None = None
    in_template_block = False
    replaced = 0

    for line in lines:
        role_match = re.match(r'\s{4}"(.+?)":\s*\{', line)
        if role_match:
            current_role = role_match.group(1)

        if current_role and not in_template_block and '"template"' in line:
            templates = _collect_templates(current_role)
            if templates:
                indent_match = re.match(r'(\s*)"template"', line)
                indent = indent_match.group(1) if indent_match else "        "
                output.append(f'{indent}"template": [\n')
                for template in templates:
                    output.append(f'{indent}    "{template}",\n')
                output.append(f'{indent}],\n')
                replaced += 1
                if "[" in line and "]" in line:
                    continue
                in_template_block = True
                continue

        if in_template_block:
            if re.search(r"\],\s*$", line):
                in_template_block = False
            continue

        if re.match(r"\s{4}\},\s*$", line):
            current_role = None

        output.append(line)

    if replaced == 0:
        return 0

    LOADSETTING_PATH.write_text("".join(output), encoding="utf-8")
    return replaced


def main() -> int:
    if not LOADSETTING_PATH.is_file():
        print(f"找不到配置文件: {LOADSETTING_PATH}")
        return 1
    if not TEMPLATE_ROOT.is_dir():
        print(f"找不到模板目录: {TEMPLATE_ROOT}")
        return 1

    replaced = _update_loadsetting()
    if replaced == 0:
        print("未替换任何模板条目（可能路径不匹配或没有图片）。")
        return 0

    print(f"已更新 {replaced} 个角色的 template。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
