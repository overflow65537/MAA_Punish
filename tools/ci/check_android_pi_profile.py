#!/usr/bin/env python3
"""校验 Android 打包配方装得下 interface.json 引用的文件。

MaaFwApp 在构建期按 `.github/android/pi-profile.yaml` 的 include/exclude 把 PI 装进
assets/pi.zip，设备上再解包到 `files/pi`。配方没覆盖的文件在 Android 上就等于不存在：
import 分片读不到只会降级成警告并跳过（该分片的 option/setting 整体消失），
而桌面端是整份复制，所以这个缺口在桌面端永远暴露不出来。

本脚本只检查客户端加载 PI 时必然要读的那几类文件（import 分片、languages、icon、
license、agent 脚本入口），resource/ 与 agent/ 的载荷由配方里的整目录 glob 负责。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE = REPO_ROOT / ".github" / "android" / "pi-profile.yaml"

PROJECT_DIR_PLACEHOLDER = "{PROJECT_DIR}/"


def parse_profile_lists(text: str) -> tuple[list[str], list[str]]:
    """只取顶层 include / exclude 两个列表，够用且不用为一份配方引入 YAML 依赖。"""
    include: list[str] = []
    exclude: list[str] = []
    current: list[str] | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line[:1].isspace():
            key = stripped.split("#", 1)[0].strip()
            if key == "include:":
                current = include
            elif key == "exclude:":
                current = exclude
            else:
                current = None
            continue
        if current is None or not stripped.startswith("- "):
            continue
        current.append(stripped[2:].strip().strip("'\""))
    return include, exclude


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Gradle/Ant 风格的相对路径 glob：`**` 跨目录，`*`/`?` 不跨。"""
    out: list[str] = []
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if char == "*":
            if pattern.startswith("**", i):
                i += 2
                if pattern.startswith("/", i):
                    i += 1
                    out.append("(?:.*/)?")
                else:
                    out.append(".*")
            else:
                i += 1
                out.append("[^/]*")
        elif char == "?":
            i += 1
            out.append("[^/]")
        else:
            i += 1
            out.append(re.escape(char))
    return re.compile("^" + "".join(out) + "$")


def normalize(entry: str) -> str:
    path = entry.strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path.lstrip("/")


def collect_references(interface: dict[str, object]) -> list[tuple[str, str]]:
    """(用途, 相对路径)；只收加载期必须读到的文件。"""
    refs: list[tuple[str, str]] = []

    imports = interface.get("import")
    if isinstance(imports, list):
        for entry in imports:
            if isinstance(entry, str):
                refs.append(("import", normalize(entry)))

    languages = interface.get("languages")
    if isinstance(languages, dict):
        for lang, entry in languages.items():
            if isinstance(entry, str):
                refs.append((f"languages.{lang}", normalize(entry)))

    for key in ("icon", "license"):
        entry = interface.get(key)
        if isinstance(entry, str) and not entry.startswith(("http://", "https://", "$")):
            refs.append((key, normalize(entry)))

    agent = interface.get("agent")
    if isinstance(agent, dict):
        args = agent.get("child_args")
        if isinstance(args, list):
            for entry in args:
                if isinstance(entry, str) and entry.startswith(PROJECT_DIR_PLACEHOLDER):
                    refs.append(("agent.child_args", normalize(entry[len("{PROJECT_DIR}") :])))
        for key in ("child_exec",):
            entry = agent.get(key)
            if isinstance(entry, str) and entry.startswith(PROJECT_DIR_PLACEHOLDER):
                refs.append(("agent.child_exec", normalize(entry[len("{PROJECT_DIR}") :])))

    return refs


def main() -> int:
    if not PROFILE.is_file():
        print(f"[error] 找不到 Android 打包配方：{PROFILE.relative_to(REPO_ROOT)}")
        return 1

    include, exclude = parse_profile_lists(PROFILE.read_text(encoding="utf-8"))
    if not include:
        print("[error] 配方里没有 include 列表")
        return 1

    # 配方里的 assets 相对配方文件所在目录
    assets_entry = ""
    for line in PROFILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("assets:"):
            assets_entry = line.split(":", 1)[1].split("#", 1)[0].strip().strip("'\"")
            break
    assets_dir = (PROFILE.parent / assets_entry).resolve() if assets_entry else REPO_ROOT

    interface_path = assets_dir / "interface.json"
    if not interface_path.is_file():
        print(f"[error] 配方 assets 指向的位置没有 interface.json：{assets_dir}")
        return 1
    interface = json.loads(interface_path.read_text(encoding="utf-8"))

    include_patterns = [(pattern, glob_to_regex(pattern)) for pattern in include]
    exclude_patterns = [(pattern, glob_to_regex(pattern)) for pattern in exclude]

    errors: list[str] = []

    def packaged(relative: str) -> bool:
        if not any(regex.match(relative) for _, regex in include_patterns):
            return False
        return not any(regex.match(relative) for _, regex in exclude_patterns)

    for purpose, relative in collect_references(interface):
        if not packaged(relative):
            errors.append(f"{purpose}: {relative} 不在 Android 打包范围内（include 未覆盖或被 exclude 挖掉）")
        elif not (assets_dir / relative).is_file():
            errors.append(f"{purpose}: {relative} 在仓库里不存在")

    # 顺手挡住配方手滑：include 里写错的首段目录/文件
    seen: set[str] = set()
    for pattern in include:
        head = pattern.split("/", 1)[0]
        if head in seen or any(char in head for char in "*?[]"):
            continue
        seen.add(head)
        if not (assets_dir / head).exists():
            errors.append(f"include: {pattern} 指向的 {head} 在仓库里不存在")

    if errors:
        print(f"Android 打包配方校验失败（{PROFILE.relative_to(REPO_ROOT)}）：")
        for error in errors:
            print(f"  - {error}")
        print("\n注：设备端只会把这些缺失报成 warning 并跳过，表现为对应选项/分片整体消失。")
        return 1

    print(f"Android 打包配方校验通过：{len(include)} 条 include 覆盖了 interface.json 的加载期引用。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
