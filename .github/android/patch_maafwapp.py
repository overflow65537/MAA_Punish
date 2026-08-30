#!/usr/bin/env python3
"""将 MaaFwApp 的 applicationId 基础包名改为 MAA_Punish 使用的命名空间。"""

from __future__ import annotations

import argparse
from pathlib import Path

RELATIVE_TARGET = Path(
    "build-logic/convention/src/main/kotlin/com/aliothmoon/maafw/gradle/"
    "AndroidApplicationConventionPlugin.kt"
)
OLD = 'private const val BASE_APPLICATION_ID = "com.aliothmoon.maafw"'
NEW = 'private const val BASE_APPLICATION_ID = "com.overflow65537.maafw"'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("maafwapp", type=Path, help="MaaFwApp 仓库根目录")
    args = parser.parse_args()

    target = args.maafwapp.resolve() / RELATIVE_TARGET
    if not target.is_file():
        raise SystemExit(f"MaaFwApp applicationId 配置文件不存在: {target}")

    content = target.read_text(encoding="utf-8")
    old_count = content.count(OLD)
    new_count = content.count(NEW)

    if old_count == 1 and new_count == 0:
        target.write_text(content.replace(OLD, NEW), encoding="utf-8")
    elif old_count == 0 and new_count == 1:
        pass
    else:
        raise SystemExit(
            "无法安全修改 MaaFwApp 基础包名："
            f"旧配置出现 {old_count} 次，新配置出现 {new_count} 次。"
            "请检查上游构建逻辑是否已经变化。"
        )

    print("Android applicationId base: com.overflow65537.maafw")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
