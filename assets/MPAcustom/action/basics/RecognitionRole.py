"""
MAA_Punish
MAA_Punish 在战斗中识别角色
作者:overflow65537
"""

from maa.context import Context
from maa.custom_action import CustomAction
from MPAcustom.action.tool.LoadSetting import ROLE_ACTIONS
from MPAcustom.logger_component import LoggerComponent


class RecognitionRole(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        logger_component = LoggerComponent(__name__)
        logger = logger_component.logger
        logger.info("开始识别角色")
        image = context.tasker.controller.post_screencap().wait().get()
        for role_name, role_info in ROLE_ACTIONS.items():
            context.run_action("攻击")
            result = context.run_recognition(
                entry="检查角色",
                image=image,
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

            if result and result.hit:
                context.override_pipeline(
                    {
                        "战斗中": {
                            "action": "Custom",
                            "custom_action": role_info["cls_name"],
                        },
                    }
                )
                logger.info(f"识别到角色: {role_name}")
                return CustomAction.RunResult(success=True)
        logger.info("未识别到角色，使用默认战斗流程")
        context.override_pipeline(
            {
                "战斗中": {
                    "action": "Custom",
                    "custom_action": "GeneralFight",
                },
            }
        )

        return CustomAction.RunResult(success=True)
