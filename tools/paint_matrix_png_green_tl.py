#!/usr/bin/env python3
"""
读取文件夹中的 PNG，在左上角涂绿色矩形，按文件名区分规则：

- 文件名含「矩阵」：以左上角为基准，宽 58、高 20（约 82×82 矩阵头像模板）
- 文件名不含「矩阵」：以左上角为基准，宽 39、高 19

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

MATRIX_MARKER = "矩阵"
MATRIX_RECT = (58, 20)
NON_MATRIX_RECT = (39, 19)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="PNG 左上角涂绿：含「矩阵」58×20，否则 39×19"
    )
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
        "--matrix-size",
        type=int,
        nargs=2,
        metavar=("W", "H"),
        default=(82, 82),
        help="含「矩阵」图片期望宽高（默认 82 82）",
    )
    p.add_argument(
        "--size-tol",
        type=int,
        default=8,
        help="含「矩阵」图片宽高允许偏差像素（默认 8）",
    )
    p.add_argument(
        "--matrix-rect",
        type=int,
        nargs=2,
        metavar=("W", "H"),
        default=MATRIX_RECT,
        help="含「矩阵」左上角矩形宽高（默认 58 20）",
    )
    p.add_argument(
        "--non-matrix-rect",
        type=int,
        nargs=2,
        metavar=("W", "H"),
        default=NON_MATRIX_RECT,
        help="不含「矩阵」左上角矩形宽高（默认 39 19）",
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


def rect_for_name(name: str, args: argparse.Namespace) -> tuple[int, int]:
    if MATRIX_MARKER in name:
        return tuple(args.matrix_rect)
    return tuple(args.non_matrix_rect)


def passes_size_check(name: str, w: int, h: int, args: argparse.Namespace) -> bool:
    if MATRIX_MARKER not in name:
        return True
    tw, th = args.matrix_size
    tol = args.size_tol
    return abs(w - tw) <= tol and abs(h - th) <= tol


def main() -> int:
    args = parse_args()
    folder = args.folder.expanduser().resolve()
    if not folder.is_dir():
        print(f"错误: 不是文件夹: {folder}", file=sys.stderr)
        return 1

    r, g, b = args.rgb

    if args.in_place:
        out_root = None
    elif args.output_dir is not None:
        out_root = args.output_dir.expanduser().resolve()
        out_root.mkdir(parents=True, exist_ok=True)
    else:
        out_root = folder.parent / "painted_green_tl"
        out_root.mkdir(parents=True, exist_ok=True)

    processed_matrix = 0
    processed_non_matrix = 0
    skipped_size = 0

    recursive = not args.flat
    for png in iter_pngs(folder, recursive):
        img = Image.open(png)
        w, h = img.size
        if not passes_size_check(png.name, w, h, args):
            tw, th = args.matrix_size
            print(
                f"跳过尺寸 {w}x{h}（含「矩阵」时期望约 {tw}x{th}±{args.size_tol}）: {png}"
            )
            skipped_size += 1
            img.close()
            continue

        rw, rh = rect_for_name(png.name, args)
        is_matrix = MATRIX_MARKER in png.name

        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        else:
            img = img.copy()

        draw = ImageDraw.Draw(img)
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
        kind = "矩阵" if is_matrix else "非矩阵"
        print(f"已写入 [{kind} {rw}x{rh}]: {dest}")
        if is_matrix:
            processed_matrix += 1
        else:
            processed_non_matrix += 1

    total = processed_matrix + processed_non_matrix
    print(
        f"完成: 处理 {total} 张"
        f"（含「矩阵」{processed_matrix} 张 {args.matrix_rect[0]}×{args.matrix_rect[1]}，"
        f"不含「矩阵」{processed_non_matrix} 张 {args.non_matrix_rect[0]}×{args.non_matrix_rect[1]}）；"
        f"因尺寸跳过 {skipped_size}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
