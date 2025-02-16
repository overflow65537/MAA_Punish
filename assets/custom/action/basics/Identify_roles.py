from maa.context import Context
from maa.custom_action import CustomAction


class Identify_roles(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        image = context.tasker.controller.post_screencap().wait().get()

        role_action_mapping = {
            "终焉": "Oblivion",
            "深痕": "Stigmata",
            "深谣": "LostLullaby",
            "深红囚影": "CrimsonWeave",
            "誓焰": "Pyroath",
        }

        # 识别三位角色名
        recognition_results = {
            "first_role_name": context.run_recognition("识别第一位角色名", image).best_result.text,
            "second_role_name": context.run_recognition("识别第二位角色名", image).best_result.text,
            "third_role_name": context.run_recognition("识别第三位角色名", image).best_result.text,
        }

        # 检查哪些角色名在映射中，并构建matched_roles字典
        matched_roles = {}
        for key, role_name in recognition_results.items():
            if role_name in role_action_mapping:
                # 这里存储的是映射后的动作，而不是角色名，例：key:first_role_name，value:Oblivion
                matched_roles[key] = role_action_mapping[role_name]

        # 处理单个角色匹配的情况
        if len(matched_roles) == 1:
            # 获取动作名
            role_key, role_value = next(iter(matched_roles.items()))  # 获取字典中的一个项（键，值）
            context.override_pipeline(
                {
                    "识别人物": {"enabled": False},
                    "战斗中": {"action": "Custom", "custom_action": role_action_mapping[role_value]},
                }
            )

        # 处理多个角色匹配的情况
        elif len(matched_roles) > 1:
            pass
        else:
            print("No matched roles for teaming up.")
        return CustomAction.RunResult(success=True)
