# 获取当前文件的目录
import json
import os

# # 获取当前文件的目录
current_dir = os.path.dirname(__file__)
# 构造 JSON 文件的路径
json_file_path = os.path.join(current_dir, '..', 'setting.json')

# 读取 JSON 文件的函数，专注于 ROLE_ACTIONS
def load_role_actions():
    with open(json_file_path, 'r', encoding='utf-8') as file:
        settings = json.load(file)
    return settings.get("ROLE_ACTIONS", {})  # 直接获取 ROLE_ACTIONS