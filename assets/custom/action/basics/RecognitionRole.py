"""
MAA_Punish
MAA_Punish 在战斗中识别角色
作者:overflow65537
"""

from maa.context import Context
from maa.custom_action import CustomAction
from custom.action.tool.LoadSetting import ROLE_ACTIONS


class RecognitionRole(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:

        for role_name, role_info in ROLE_ACTIONS.items():
            result = context.run_recognition(
                entry="检查角色",
                image=context.tasker.controller.post_screencap().wait().get(),
                pipeline_override={
                    "检查角色": {
                        "recognition": {
                            "param": {
                                "template": role_info["attack_template"],
                            },
                        }
                    }
                },
            )
            if result:
                context.override_pipeline(
                    {
                        "识别人物": {"enabled": False},
                        "战斗中": {
                            "action": "Custom",
                            "custom_action": role_info["cls_name"],
                        },
                    }
                )
                return CustomAction.RunResult(success=True)
        context.override_pipeline(
            {
                "识别人物": {"enabled": True},
                "战斗中": {"action": "Custom",
                            "custom_action": "GeneralFight",},
            }
        )

        return CustomAction.RunResult(success=True)
