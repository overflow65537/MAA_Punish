"""
按 pipeline 节点 ROI 与 win32 标准锚点区重合关系归类（供生成工具使用）。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .roi_zone_controller import REFERENCE_ZONE_RECTS

_PIPELINE_ROOT = (
    Path(__file__).resolve().parents[4] / "resource" / "base" / "pipeline"
)
COMBAT_PIPELINE_DIR = _PIPELINE_ROOT / "Auto_Battle"
POINT_ZONE_MARGIN = 48
OFFSET_EXCLUDED_NODES = frozenset({"战斗中"})


def expand_rect(rect: list[int], margin: int) -> list[int]:
    x, y, w, h = rect
    return [x - margin, y - margin, w + margin * 2, h + margin * 2]


def rect_bounds(rect: list[int]) -> tuple[int, int, int, int]:
    x, y, w, h = [int(v) for v in rect]
    return x, y, x + max(w, 0), y + max(h, 0)


def intersection_area(a: list[int], b: list[int]) -> int:
    ax1, ay1, ax2, ay2 = rect_bounds(a)
    bx1, by1, bx2, by2 = rect_bounds(b)
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0
    return (ix2 - ix1) * (iy2 - iy1)


def point_in_rect(x: int, y: int, rect: list[int]) -> bool:
    x1, y1, x2, y2 = rect_bounds(rect)
    return x1 <= x <= x2 and y1 <= y <= y2


def extract_classify_rect(node: dict[str, Any]) -> list[int] | None:
    recognition = node.get("recognition")
    if isinstance(recognition, dict):
        param = recognition.get("param")
        if isinstance(param, dict):
            roi = param.get("roi")
            if (
                isinstance(roi, list)
                and len(roi) == 4
                and all(isinstance(v, (int, float)) for v in roi)
            ):
                return [int(v) for v in roi]

    action = node.get("action")
    if isinstance(action, dict):
        param = action.get("param")
        if isinstance(param, dict):
            for key in ("target", "begin"):
                point = param.get(key)
                if (
                    isinstance(point, list)
                    and len(point) in (2, 4)
                    and all(isinstance(v, (int, float)) for v in point)
                ):
                    return [int(v) for v in point]
    return None


def _center_dist_to_rect(cx: int, cy: int, rect: list[int]) -> int:
    x1, y1, x2, y2 = rect_bounds(rect)
    dx = 0 if x1 <= cx <= x2 else min(abs(cx - x1), abs(cx - x2))
    dy = 0 if y1 <= cy <= y2 else min(abs(cy - y1), abs(cy - y2))
    return dx + dy


def _action_zone_penalty(zone_key: str, cy: int, zone_rect: list[int]) -> int:
    if zone_key not in {"atk_zone", "dodge_zone", "skill_zone"}:
        return 0
    _, y1, _, _ = rect_bounds(zone_rect)
    return 1 if cy < y1 else 0


def classify_zone_key(rect: list[int]) -> str | None:
    if len(rect) == 2:
        px, py = int(rect[0]), int(rect[1])
        for zone_key, zone_rect in REFERENCE_ZONE_RECTS.items():
            if point_in_rect(px, py, expand_rect(zone_rect, POINT_ZONE_MARGIN)):
                return zone_key
        return None

    if len(rect) == 4 and rect[2] == 0 and rect[3] == 0:
        return classify_zone_key([rect[0], rect[1]])

    w, h = max(int(rect[2]), 0), max(int(rect[3]), 0)
    node_area = w * h
    if node_area <= 0:
        return classify_zone_key([int(rect[0]), int(rect[1])])

    best_key: str | None = None
    best_score = 0.0
    for zone_key, zone_rect in REFERENCE_ZONE_RECTS.items():
        area = intersection_area(rect, zone_rect)
        if area <= 0:
            continue
        zone_area = max(int(zone_rect[2]), 0) * max(int(zone_rect[3]), 0)
        if zone_area <= 0:
            continue
        score = area / min(node_area, zone_area)
        if score > best_score:
            best_score = score
            best_key = zone_key

    if best_key is not None and best_score >= 0.5:
        return best_key

    best_key = None
    best_score = 0.0
    best_rank: tuple[int, int, int] | None = None
    cx = int(rect[0]) + w // 2
    cy = int(rect[1]) + h // 2
    for zone_key, zone_rect in REFERENCE_ZONE_RECTS.items():
        area = intersection_area(rect, expand_rect(zone_rect, POINT_ZONE_MARGIN))
        if area <= 0:
            continue
        zone_area = max(int(zone_rect[2]), 0) * max(int(zone_rect[3]), 0)
        if zone_area <= 0:
            continue
        score = area / min(node_area, zone_area)
        rank = (
            -int(score * 1000),
            _action_zone_penalty(zone_key, cy, zone_rect),
            _center_dist_to_rect(cx, cy, zone_rect),
        )
        if best_rank is None or rank < best_rank:
            best_rank = rank
            best_score = score
            best_key = zone_key

    if best_key is not None and best_score >= 0.5:
        return best_key

    best_key = None
    best_dist = None
    best_penalty: int | None = None
    for zone_key, zone_rect in REFERENCE_ZONE_RECTS.items():
        dist = _center_dist_to_rect(cx, cy, zone_rect)
        if dist > POINT_ZONE_MARGIN:
            continue
        penalty = _action_zone_penalty(zone_key, cy, zone_rect)
        rank = (penalty, dist)
        if best_dist is None or rank < (best_penalty, best_dist):
            best_penalty = penalty
            best_dist = dist
            best_key = zone_key
    return best_key


def load_combat_pipeline_nodes() -> dict[str, dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    if not COMBAT_PIPELINE_DIR.is_dir():
        return nodes

    for path in COMBAT_PIPELINE_DIR.rglob("*"):
        if path.suffix not in {".json", ".jsonc"}:
            continue
        text = re.sub(r"//.*", "", path.read_text(encoding="utf-8"))
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        for name, node in data.items():
            if isinstance(node, dict):
                nodes[name] = node
    return nodes


def build_node_zone_map() -> dict[str, str]:
    zone_map: dict[str, str] = {}
    for name, node in load_combat_pipeline_nodes().items():
        if name in OFFSET_EXCLUDED_NODES:
            continue
        rect = extract_classify_rect(node)
        if rect is None:
            continue
        zone_key = classify_zone_key(rect)
        if zone_key is not None:
            zone_map[name] = zone_key
    return dict(sorted(zone_map.items()))
