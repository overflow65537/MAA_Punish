#!/usr/bin/env python3
"""
将 interface.json 中的 task 和 option 拆分为独立文件。

规则：
- 每个 task 单独一个文件，存放于 assets/tasks/，文件名以 task 的 name 命名：{name}.json
- 每个文件包含：task 本身 + 该 task.option 中列出的选项定义
- 从 interface.json 中删除已拆分的 task 和这些 option
- 在 interface.json 中新增 import 列表，每项为以 assets 为基准的路径，如 .\\tasks\\进入游戏.json
"""

import json
import re
from pathlib import Path


def sanitize_filename(name: str) -> str:
    """将 task 名称转为安全文件名（保留中文等，仅替换非法字符）。"""
    # Windows 非法字符: \ / : * ? " < > |
    unsafe = r'[\\/:*?"<>|]'
    return re.sub(unsafe, "_", name)


def main():
    base = Path(__file__).resolve().parent.parent
    interface_path = base / "assets" / "interface.json"
    tasks_dir = base / "assets" / "tasks"

    tasks_dir.mkdir(parents=True, exist_ok=True)

    with open(interface_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tasks = data.get("task", [])
    global_options = data.get("option", {})

    if not tasks:
        print("没有需要拆分的 task。")
        return

    import_list = []
    options_to_remove = set()

    for task in tasks:
        name = task.get("name")
        if not name:
            continue
        option_names = task.get("option", [])
        # 该 task 对应的 option 定义（只包含本 task 引用的）
        task_options = {}
        for opt_name in option_names:
            if opt_name in global_options:
                task_options[opt_name] = global_options[opt_name]
                options_to_remove.add(opt_name)

        out_obj = {
            "task": [task],
            "option": task_options,
        }
        safe_name = sanitize_filename(name)
        out_path = tasks_dir / f"{safe_name}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out_obj, f, ensure_ascii=False, indent=4)

        # 以 assets 为基准的路径，使用反斜杠
        import_list.append(".\\tasks\\" + safe_name + ".json")
        print(f"已写入: {out_path.relative_to(base)}")

    # 从 interface 中清空 task，并在 task 之后添加 import
    data["task"] = []
    # 从 interface 的 option 中移除已拆分到各 task 文件中的选项
    for key in options_to_remove:
        if key in data["option"]:
            del data["option"][key]

    # 保证 import 紧跟在 task 之后（重建 key 顺序）
    new_data = {}
    for k in data.keys():
        if k == "import":
            continue
        new_data[k] = data[k]
        if k == "task":
            new_data["import"] = import_list

    with open(interface_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)

    print(f"已更新 interface.json：task 已清空，已添加 import（共 {len(import_list)} 项），已移除 {len(options_to_remove)} 个 option。")


if __name__ == "__main__":
    main()
