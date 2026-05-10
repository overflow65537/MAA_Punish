#!/usr/bin/env python3
"""
读取文件夹中的 PNG，筛选文件名含「_矩阵」且尺寸约 82×82 的图片，
将左上角 58×20 区域涂成绿色。

依赖: pip install pillow

用法:
  python paint_matrix_png_green_tl.py D:\\path\\to\\folder
  python paint_matrix_png_green_tl.py --in-place
  python paint_matrix_png_green_tl.py D:\\path\\to\\folder -o D:\\out

省略路径时默认处理「当前工作目录」。默认递归子目录；若只需当前目录可加 --flat。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="将「_矩阵」PNG 左上角 58×20 涂绿")
    p.add_argument(
        "folder",
        type=Path,
        nargs="?",
        default=Path("."),
        help="图片所在文件夹（省略则为当前工作目录）",
    )
    p.add_argument(
        "--flat",
        "--no-recursive",
        action="store_true",
        help="仅搜索当前目录下的 PNG，不进入子目录（默认递归子目录）",
    )
    p.add_argument(
        "--in-place",
        action="store_true",
        help="直接覆盖原文件（慎用）",
    )
    p.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="输出目录（默认与输入同级目录下的 painted_green_tl）",
    )
    p.add_argument(
        "--marker",
        default="矩阵_",
        help="文件名需包含的子串（默认: _矩阵）",
    )
    p.add_argument(
        "--size",
        type=int,
        nargs=2,
        metavar=("W", "H"),
        default=(82, 82),
        help="期望宽高（默认 82 82）",
    )
    p.add_argument(
        "--size-tol",
        type=int,
        default=8,
        help="宽高允许偏差像素（默认 8）",
    )
    p.add_argument(
        "--rect",
        type=int,
        nargs=2,
        metavar=("W", "H"),
        default=(58, 20),
        help="左上角矩形宽高（默认 58 20）",
    )
    p.add_argument(
        "--rgb",
        type=int,
        nargs=3,
        metavar=("R", "G", "B"),
        default=(0, 255, 0),
        help="绿色 RGB（默认 0 255 0）",
    )
    return p.parse_args()


def iter_pngs(root: Path, recursive: bool):
    pattern = "**/*.png" if recursive else "*.png"
    yield from sorted(root.glob(pattern))


def main() -> int:
    args = parse_args()
    folder = args.folder.expanduser().resolve()
    if not folder.is_dir():
        print(f"错误: 不是文件夹: {folder}", file=sys.stderr)
        return 1

    tw, th = args.size
    tol = args.size_tol
    rw, rh = args.rect
    r, g, b = args.rgb

    if args.in_place:
        out_root = None
    elif args.output_dir is not None:
        out_root = args.output_dir.expanduser().resolve()
        out_root.mkdir(parents=True, exist_ok=True)
    else:
        out_root = folder.parent / "painted_green_tl"
        out_root.mkdir(parents=True, exist_ok=True)

    processed = 0
    skipped_size = 0
    skipped_name = 0

    recursive = not args.flat
    for png in iter_pngs(folder, recursive):
        if args.marker not in png.name:
            skipped_name += 1
            continue

        img = Image.open(png)
        w, h = img.size
        if abs(w - tw) > tol or abs(h - th) > tol:
            print(f"跳过尺寸 {w}x{h}（期望约 {tw}x{th}±{tol}）: {png}")
            skipped_size += 1
            img.close()
            continue

        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        else:
            img = img.copy()

        draw = ImageDraw.Draw(img)
        # 左上角矩形 [0, 0, rw-1, rh-1] 共 rw×rh 像素
        draw.rectangle(
            [0, 0, rw - 1, rh - 1],
            fill=(r, g, b, 255) if img.mode == "RGBA" else (r, g, b),
        )

        if args.in_place:
            dest = png
        else:
            assert out_root is not None
            rel = png.relative_to(folder)
            dest = out_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)

        img.save(dest, format="PNG")
        img.close()
        print(f"已写入: {dest}")
        processed += 1

    print(
        f"完成: 处理 {processed} 张；"
        f"因尺寸跳过 {skipped_size}；"
        f"因文件名不含「{args.marker}」略过 {skipped_name} 个文件（仍扫描了目录内 png）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
