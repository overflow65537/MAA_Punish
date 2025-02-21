import time

from maa.context import Context
from maa.custom_action import CustomAction

#2025.2.21适配任意单人角色识别（待进行代码优化）

class Identify_roles(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        role_action_mapping = {
            "露娜·终焉": "Oblivion",
            "比安卡·深痕": "Stigmata",
            "拉弥亚·深谣": "LostLullaby",
            "露西亚·深红囚影": "CrimsonWeave",
            "露西亚·誓焰": "Pyroath",
        }

        # 位置映射角色名
        recognition_results = {}

        # 位置映射队长角色
        location_results = {}

        context.run_task("点击更换")

        # 识别角色名
        image = context.tasker.controller.post_screencap().wait().get()
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

        # 识别当前队长位置
        first_location = context.run_recognition("识别第一个队长位置", image)
        second_location = context.run_recognition("识别第二个队长位置", image)
        third_location = context.run_recognition("识别第三个队长位置", image)
        if first_location is not None:
            location_results["first_location"] = first_location.best_result.text
        if second_location is not None:
            location_results["second_location"] = second_location.best_result.text
        if third_location is not None:
            location_results["third_location"] = third_location.best_result.text

        print(location_results)

        context.run_task("出队长界面")
        # 检查哪些角色名在映射中，并构建matched_roles字典
        matched_roles = {}
        for key, role_name in recognition_results.items():
            if role_name in role_action_mapping:
                # 这里存储的是映射后的动作，而不是角色名，例：key:first_role_name，value:Oblivion
                matched_roles[key] = role_action_mapping[role_name]

        # 处理单个角色匹配的情况
        if len(matched_roles) == 1:
            # 处理队长位置匹配首选角色
            if "first_location" in location_results:
                context.run_task("点击首选位置", {"点击首选位置": {"expected": "蓝色"}})
            if "second_location" in location_results:
                context.run_task("点击首选位置", {"点击首选位置": {"expected": "红色"}})
            if "third_location" in location_results:
                context.run_task("点击首选位置", {"点击首选位置": {"expected": "黄色"}})

            # 获取动作名
            role_key, role_value = next(iter(matched_roles.items()))  # 获取字典中的一个项（键，值）
            context.override_pipeline(
                {
                    "角色特有战斗": {"action": "Custom", "custom_action": role_value},
                }
            )

        # 处理多个角色匹配的情况
        elif len(matched_roles) > 1:
            print("这是多角色,测试提示")
        else:
            print("No matched roles for teaming up.")

        return CustomAction.RunResult(success=True)
