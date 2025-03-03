import json
import os
from pathlib import Path
import sys

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
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