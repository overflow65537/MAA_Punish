from maa.context import Context
from maa.custom_action import CustomAction


class Identify(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        image = context.tasker.controller.post_screencap().wait().get()
        if context.run_recognition("检查终焉", image):
            context.override_pipeline(
                {
                    "识别人物": {"enabled": False},
                    "战斗中": {"action": "Custom", "custom_action": "Oblivion"},
                }
            )
            print("终焉战斗")
        elif context.run_recognition("检查深痕", image):
            context.override_pipeline(
                {
                    "识别人物": {"enabled": False},
                    "战斗中": {"action": "Custom", "custom_action": "Stigmata"},
                }
            )
            print("深痕战斗")
        elif context.run_recognition("检查深谣", image):
            context.override_pipeline(
                {
                    "识别人物": {"enabled": False},
                    "战斗中": {"action": "Custom", "custom_action": "LostLullaby"},
                }
            )
            print("深谣战斗")
        elif context.run_recognition("检查深红囚影", image):
            context.override_pipeline(
                {
                    "识别人物": {"enabled": False},
                    "战斗中": {"action": "Custom", "custom_action": "CrimsonWeave"},
                }
            )
            print("深红囚影")
        elif context.run_recognition("检查誓焰", image):
            context.override_pipeline(
                {
                    "识别人物": {"enabled": False},
                    "战斗中": {"action": "Custom", "custom_action": "Pyroath"},
                }
            )
            print("誓焰战斗")
        return CustomAction.RunResult(success=True)
