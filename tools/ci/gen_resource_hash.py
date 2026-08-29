"""通过 maafw 计算 interface.resource 的 hash，并写入各 resource.hash 字段。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import jsonc
from maa.resource import Resource

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMENT_BEGIN = "<!-- mfw-resource-hash"
COMMENT_END = "-->"


def compute_resource_hash(paths: list[str], root: Path) -> str:
    resource = Resource()
    for raw_path in paths:
        normalized = raw_path.removeprefix("./")
        bundle_path = (root / normalized).resolve()
        if not bundle_path.is_dir():
            raise FileNotFoundError(f"resource bundle not found: {bundle_path}")
        status = resource.post_bundle(bundle_path).wait()
        if not status.succeeded:
            raise RuntimeError(f"failed to load resource bundle: {bundle_path}")

    hash_value = resource.hash
    if callable(hash_value):
        hash_value = hash_value()
    result = str(hash_value or "").strip()
    if not result:
        raise RuntimeError("maafw returned empty resource hash")
    return result


def build_hash_comment(lines: list[tuple[str, str]]) -> str:
    body = "\n".join(f"{name}: {hash_value}" for name, hash_value in lines)
    return f"{COMMENT_BEGIN}\n{body}\n{COMMENT_END}"


def apply_resource_hashes(
    interface_path: Path,
    *,
    root: Path = REPO_ROOT,
) -> str:
    with open(interface_path, encoding="utf-8") as handle:
        interface = jsonc.load(handle)

    comment_lines: list[tuple[str, str]] = []
    for entry in interface.get("resource", []):
        if not isinstance(entry, dict):
            continue
        raw_paths = entry.get("path")
        if not isinstance(raw_paths, list) or not raw_paths:
            continue

        paths = [str(path) for path in raw_paths]
        hash_value = compute_resource_hash(paths, root)
        entry["hash"] = hash_value

        name = entry.get("name")
        comment_lines.append((str(name) if name else "resource", hash_value))

    with open(interface_path, "w", encoding="utf-8") as handle:
        jsonc.dump(interface, handle, ensure_ascii=False, indent=4)
        handle.write("\n")

    return build_hash_comment(comment_lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "interface",
        nargs="?",
        type=Path,
        default=REPO_ROOT / "interface.json",
        help="interface.json 路径，默认仓库根目录",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="资源路径解析根目录",
    )
    args = parser.parse_args()

    interface_path = args.interface.resolve()
    if not interface_path.is_file():
        print(f"interface.json not found: {interface_path}", file=sys.stderr)
        return 1

    comment = apply_resource_hashes(interface_path, root=args.root.resolve())
    print(comment)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
