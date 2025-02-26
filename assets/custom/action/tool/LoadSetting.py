import json
import os


class LoadSetting:

    def load_role_setting():
        with open(os.path.join(os.path.dirname(__file__), '..', 'setting.json'), 'r', encoding='utf-8') as file:
            return json.load(file).get("ROLE_ACTIONS", {})