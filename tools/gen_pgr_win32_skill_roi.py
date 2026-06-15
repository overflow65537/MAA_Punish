#!/usr/bin/env python3
"""Generate pgr_win32 Check_Characters_Skill/*.jsonc with ROI-only overrides."""

from __future__ import annotations

import json
from pathlib import Path


def strip_jsonc_comments(text: str) -> str:
    result: list[str] = []
    state = 0
    i = 0
    while i < len(text):
        char = text[i]
        if state == 0:
            if char == '"':
                result.append(char)
                state = 1
                i += 1
            elif i + 1 < len(text) and text[i : i + 2] == "//":
                while i < len(text) and text[i] != "\n":
                    i += 1
                if i < len(text):
                    result.append("\n")
                    i += 1
            else:
                result.append(char)
                i += 1
        elif state == 1:
            result.append(char)
            if char == "\\":
                result.append(text[i + 1])
                i += 2
            elif char == '"':
                state = 0
                i += 1
            else:
                i += 1
    return "".join(result)


def is_roi(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 4
        and all(isinstance(x, int) for x in value)
    )


def roi_override(roi: list[int]) -> dict:
    return {"recognition": {"param": {"roi": roi}}}


# Win32 已校准 ROI（有则覆盖 base 默认值）
WIN32_ROI: dict[str, list[int]] = {
    "_信号球数量": [1173, 541, 68, 20],
    "检查核心球_霁梦": [900, 412, 100, 87],
    "检查核心技能_超刻": [724, 613, 23, 24],
    "检查p1动能条_誓焰": [750, 624, 12, 10],
    "检查u3_max": [710, 622, 50, 15],
    "检查大太刀无光值_颜色": [506, 605, 35, 21],
}


def extract_roi_nodes(data: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for name, node in data.items():
        param = (node.get("recognition") or {}).get("param") or {}
        roi = param.get("roi")
        if is_roi(roi):
            out[name] = roi_override(WIN32_ROI.get(name, roi))
    return out


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    base_dir = root / "assets/resource/base/pipeline/Auto_Battle/Check_Characters_Skill"
    out_dir = root / "assets/resource/pgr_win32/pipeline/Auto_Battle/Check_Characters_Skill"
    out_dir.mkdir(parents=True, exist_ok=True)

    for old in out_dir.glob("*.jsonc"):
        old.unlink()

    for base_file in sorted(base_dir.glob("*.jsonc")):
        data = json.loads(strip_jsonc_comments(base_file.read_text(encoding="utf-8")))
        nodes = extract_roi_nodes(data)
        out_path = out_dir / base_file.name
        out_path.write_text(
            json.dumps(nodes, ensure_ascii=False, indent=4) + "\n",
            encoding="utf-8",
        )
        print(f"{out_path.name}: {len(nodes)} roi nodes")


if __name__ == "__main__":
    main()
