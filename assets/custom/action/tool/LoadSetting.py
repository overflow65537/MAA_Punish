import json
import os
import sys
from pathlib import Path

# 获取当前文件的绝对路径
current_file = Path(__file__).resolve()

# 定义可能的项目根目录相对路径
root_paths = [
    current_file.parent.parent.parent.parent.joinpath("MFW_resource"),
    current_file.parent.parent.parent.parent.parent.parent.joinpath("Bundles").joinpath("MAA_Punish"),
    current_file.parent.parent.parent.parent.parent.joinpath("assets"),
]

# 确定项目根目录
project_root = next((path for path in root_paths if path.exists()), None)
if project_root:
    print(f"项目根目录: {project_root}")
else:
    print("[错误] 找不到项目根目录")

# 添加项目根目录到sys.path
sys.path.append(str(project_root))


class LoadSetting:
    def __init__(self):
        self._role_actions = self.load_role_setting()

    @property
    def role_actions(self):
        return self._role_actions

    @staticmethod
    def load_role_setting():
        try:
            with open(os.path.join(os.path.dirname(__file__), "..", "setting.json"), "r", encoding="utf-8") as file:
                return json.load(file).get("ROLE_ACTIONS", {})
        except FileNotFoundError:
            print("setting.json 文件未找到。")
            return {}
        except json.JSONDecodeError:
            print("setting.json 文件格式错误。")
            return {}


# 角色名称到动作的映射表
ROLE_ACTIONS = LoadSetting.load_role_setting()
