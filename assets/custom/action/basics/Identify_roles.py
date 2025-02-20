from maa.context import Context
from maa.custom_action import CustomAction


class Identify_roles(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        image = context.tasker.controller.post_screencap().wait().get()

        role_action_mapping = {
            "露娜·终焉": "Oblivion",
            "比安卡·深痕": "Stigmata",
            "拉弥亚·深谣": "LostLullaby",
            "露西亚·深红囚影": "CrimsonWeave",
            "露西亚·誓焰": "Pyroath",
        }

        
        # 识别三位角色名
        recognition_results = {}
        first_role_name = context.run_recognition("识别第一位角色名", image)
        second_role_name = context.run_recognition("识别第二位角色名", image)
        third_role_name = context.run_recognition("识别第三位角色名", image)
        if first_role_name is not None:
            recognition_results["first_role_name"] = first_role_name.best_result.text
        if second_role_name is not None:
            recognition_results["second_role_name"] = second_role_name.best_result.text
        if third_role_name is not None:
            recognition_results["third_role_name"] = third_role_name.best_result.text
        
        print(recognition_results)

        
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
                    "角色特有战斗":{"action": "Custom", "custom_action": role_value},
                }
            )

        # 处理多个角色匹配的情况
        elif len(matched_roles) > 1:
            pass
        else:
            print("No matched roles for teaming up.")
        return CustomAction.RunResult(success=True)
