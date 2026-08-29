#!/usr/bin/env python3
"""扫描 Auto_Battle pipeline，按 ROI 与标准锚点区重合生成 combat_roi_zone_map.json。"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IFACE_DIR = ROOT / "agent" / "action" / "basics" / "InterfaceZone"
OUTPUT = IFACE_DIR / "combat_roi_zone_map.json"

ZONE_LABELS = {
    "atk_zone": "攻击",
    "dodge_zone": "闪避",
    "skill_zone": "大招",
    "signal_zone": "信号球",
    "corepass_zone": "核心被动",
    "assist_zone": "辅助机",
    "lock_zone": "锁定",
    "switch_zone": "换人",
}


def _load_iface_module(module_name: str, filename: str):
    pkg_names = [
        "action",
        "action.basics",
        "action.basics.InterfaceZone",
    ]
    for name in pkg_names:
        if name not in sys.modules:
            mod = types.ModuleType(name)
            mod.__path__ = []  # type: ignore[attr-defined]
            sys.modules[name] = mod
    sys.modules["action.basics.InterfaceZone"].__path__ = [str(IFACE_DIR)]  # type: ignore[attr-defined]

    full_name = f"action.basics.InterfaceZone.{module_name}"
    path = IFACE_DIR / filename
    spec = importlib.util.spec_from_file_location(full_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载 {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    _load_iface_module("roi_zone_controller", "roi_zone_controller.py")
    classify = _load_iface_module("roi_zone_classify", "roi_zone_classify.py")

    node_zone_map = classify.build_node_zone_map()
    nodes = classify.load_combat_pipeline_nodes()
    reference_zones = classify.REFERENCE_ZONE_RECTS

    payload = {
        "_generated_by": "tools/gen_combat_roi_zone_map.py",
        "reference_zones": reference_zones,
        "node_zone_map": node_zone_map,
    }
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    by_zone: dict[str, list[str]] = {k: [] for k in reference_zones}
    for name, zone_key in node_zone_map.items():
        by_zone[zone_key].append(name)

    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({len(node_zone_map)} nodes)")
    for zone_key in reference_zones:
        names = by_zone[zone_key]
        print(f"\n=== {ZONE_LABELS.get(zone_key, zone_key)} ({len(names)}) ===")
        for name in names:
            rect = classify.extract_classify_rect(nodes[name])
            print(f"  {name}: {rect}")

    unclassified = []
    for name, node in sorted(nodes.items()):
        if name in node_zone_map:
            continue
        rect = classify.extract_classify_rect(node)
        if rect is not None:
            unclassified.append((name, rect))
    if unclassified:
        print(f"\n=== 有 ROI 但未归类 ({len(unclassified)}) ===")
        for name, rect in unclassified:
            print(f"  {name}: {rect}")


if __name__ == "__main__":
    main()
