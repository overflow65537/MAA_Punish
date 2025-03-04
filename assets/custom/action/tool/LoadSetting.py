import json
import os
from pathlib import Path
import sys

# 获取当前文件的绝对路径
current_file = Path(__file__).resolve()

# 定义可能的项目根目录相对路径
MFW_root = current_file.parent.parent.parent.parent.joinpath("MFW_resource")
MAA_Punish_root = current_file.parent.parent.parent.parent.parent.parent.joinpath("Bundles")
assets_root = current_file.parent.parent.parent.parent.parent.joinpath("assets")
if MFW_root.exists():
    project_root = MFW_root
    print("MFW root")
elif MAA_Punish_root.exists():
    project_root = MAA_Punish_root.joinpath("MAA_Punish")
    print("MAA_Punish root")
elif assets_root.exists():
    project_root = assets_root
    print("assets root")

print(project_root)

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
            with open(os.path.join(os.path.dirname(__file__), '..', 'setting.json'), 'r', encoding='utf-8') as file:
                return json.load(file).get("ROLE_ACTIONS", {})
        except FileNotFoundError:
            print("setting.json 文件未找到。")
            return {}
        except json.JSONDecodeError:
            print("setting.json 文件格式错误。")
            return {}

# 角色名称到动作的映射表
ROLE_ACTIONS =  LoadSetting.load_role_setting()