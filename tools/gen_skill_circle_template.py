#!/usr/bin/env python3
"""
从 1280×720 战斗截图批量截取技能圆图标，并涂绿幕（供 TemplateMatch green_mask 使用）。

每张截图会生成两张 83×83 模板：
  - 外圆直径 83：圆外四角涂绿
  - 内圆（约直径 31，位于右下角）：圆内涂绿（可部分出界，仅处理裁剪框内像素）

默认 ROI（1280×720，格式 [x, y, w, h]）：
  外圆裁剪 1: [1173, 120, 83, 83]，内圆 [1223, 178, 31, 25]
  外圆裁剪 2: [1173, 234, 83, 83]，内圆 [1223, 292, 31, 26]

依赖: pip install pillow numpy

用法:
  python tools/gen_skill_circle_template.py D:\\screenshots
  python tools/gen_skill_circle_template.py D:\\screenshots -o D:\\out
  python tools/gen_skill_circle_template.py D:\\screenshots --flat
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

GREEN = (0, 255, 0, 255)
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


@dataclass(frozen=True)
class SlotConfig:
    name: str
    crop_roi: tuple[int, int, int, int]
    inner_roi: tuple[int, int, int, int]

    def inner_circle_in_crop(self) -> tuple[float, float, float]:
        cx, cy, cw, ch = self.crop_roi
        ix, iy, iw, ih = self.inner_roi
        rel_cx = (ix - cx) + iw / 2.0
        rel_cy = (iy - cy) + ih / 2.0
        radius = iw / 2.0
        return rel_cx, rel_cy, radius


DEFAULT_SLOTS: tuple[SlotConfig, ...] = (
    SlotConfig("1", (1173, 120, 83, 83), (1223, 178, 31, 25)),
    SlotConfig("2", (1173, 234, 83, 83), (1223, 292, 31, 26)),
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="从截图截取技能圆模板并涂绿幕")
    p.add_argument(
        "folder",
        type=Path,
        nargs="?",
        default=Path("."),
        help="截图文件夹（默认当前目录）",
    )
    p.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="输出目录（默认: 输入目录同级 skill_circle_templates）",
    )
    p.add_argument(
        "--flat",
        "--no-recursive",
        action="store_true",
        help="仅处理当前目录，不递归子目录",
    )
    p.add_argument(
        "--size",
        type=int,
        nargs=2,
        metavar=("W", "H"),
        default=(1280, 720),
        help="期望截图尺寸（默认 1280 720）",
    )
    p.add_argument(
        "--size-tol",
        type=int,
        default=0,
        help="截图尺寸允许偏差（默认 0，必须精确匹配）",
    )
    return p.parse_args()


def iter_images(root: Path, recursive: bool) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    files = [p for p in sorted(root.glob(pattern)) if p.suffix.lower() in IMAGE_EXTS]
    return files


def apply_circle_green_mask(
    crop_rgba: Image.Image,
    inner_cx: float,
    inner_cy: float,
    inner_r: float,
) -> Image.Image:
    arr = np.array(crop_rgba, dtype=np.uint8, copy=True)
    h, w = arr.shape[:2]
    if arr.shape[2] == 3:
        alpha = np.full((h, w, 1), 255, dtype=np.uint8)
        arr = np.concatenate([arr, alpha], axis=2)

    yy, xx = np.mgrid[0:h, 0:w]
    main_cx = (w - 1) / 2.0
    main_cy = (h - 1) / 2.0
    main_r = w / 2.0

    dist_main = (xx - main_cx) ** 2 + (yy - main_cy) ** 2
    dist_inner = (xx - inner_cx) ** 2 + (yy - inner_cy) ** 2

    green_mask = (dist_main > main_r * main_r) | (dist_inner <= inner_r * inner_r)
    arr[green_mask] = GREEN
    return Image.fromarray(arr, mode="RGBA")


def crop_and_mask(
    screenshot: Image.Image,
    slot: SlotConfig,
) -> Image.Image:
    x, y, w, h = slot.crop_roi
    crop = screenshot.crop((x, y, x + w, y + h)).convert("RGBA")
    inner_cx, inner_cy, inner_r = slot.inner_circle_in_crop()
    return apply_circle_green_mask(crop, inner_cx, inner_cy, inner_r)


def main() -> int:
    args = parse_args()
    folder = args.folder.expanduser().resolve()
    if not folder.is_dir():
        print(f"错误: 不是文件夹: {folder}", file=sys.stderr)
        return 1

    if args.output_dir is not None:
        out_root = args.output_dir.expanduser().resolve()
    else:
        out_root = folder.parent / "skill_circle_templates" / folder.name
    out_root.mkdir(parents=True, exist_ok=True)

    expect_w, expect_h = args.size
    tol = args.size_tol
    recursive = not args.flat

    processed = 0
    skipped_size = 0

    for img_path in iter_images(folder, recursive):
        rel = img_path.relative_to(folder)
        with Image.open(img_path) as img:
            w, h = img.size
            if abs(w - expect_w) > tol or abs(h - expect_h) > tol:
                print(f"跳过尺寸 {w}x{h}（期望 {expect_w}x{expect_h}±{tol}）: {rel}")
                skipped_size += 1
                continue
            screenshot = img.convert("RGBA")

        for slot in DEFAULT_SLOTS:
            result = crop_and_mask(screenshot, slot)
            out_name = f"{img_path.stem}_{slot.name}.png"
            if rel.parent != Path("."):
                dest = out_root / rel.parent / out_name
            else:
                dest = out_root / out_name
            dest.parent.mkdir(parents=True, exist_ok=True)
            result.save(dest, format="PNG")
            print(f"已写入: {dest}")
            processed += 1

    print(f"完成: 生成 {processed} 张模板；因尺寸跳过 {skipped_size} 张截图")
    print(f"输出目录: {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
