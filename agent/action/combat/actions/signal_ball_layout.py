"""信号球槽位布局：固定 8 格中心点，用于识别 box → 槽位索引（非点击、非 ROI）。"""

from __future__ import annotations

from typing import Any

SIGNAL_BALL_SLOT_COUNT = 8

# 与 Pipeline 消球1~8 点击位置一致；此处仅用于 TemplateMatch box 映射到槽位编号。
SIGNAL_BALL_SLOT_CENTERS: tuple[tuple[int, int], ...] = (
    (1220, 500),  # 1
    (1111, 500),  # 2
    (1003, 500),  # 3
    (894, 500),  # 4
    (786, 500),  # 5
    (677, 500),  # 6
    (569, 500),  # 7
    (460, 500),  # 8
)


def slot_index_from_box(box: Any) -> int:
    """识别 box 落在哪一号槽（0~7）；无匹配或解析失败返回 -1。"""
    try:
        x, y, w, h = box
        for idx, (pos_x, pos_y) in enumerate(SIGNAL_BALL_SLOT_CENTERS):
            if x <= pos_x <= x + w and y <= pos_y <= y + h:
                return idx
        return -1
    except (TypeError, ValueError):
        return -1
