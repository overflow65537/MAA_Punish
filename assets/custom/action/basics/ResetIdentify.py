from maa.context import Context
from maa.custom_action import CustomAction
import json


class ResetIdentify(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        argv: dict = json.loads(argv.custom_action_param)
        print(f"argv: {argv}")
        if not argv:
            context.override_pipeline({"识别人物": {"enabled": True}})

        elif argv.get("mode") == "矩阵循生":

            context.override_pipeline(
                {
                    "选择首发_矩阵循生": {"enabled": False},
                    "异度投影_矩阵循生": {"enabled": False},
                    "进入物归新主_矩阵循生": {"enabled": True},
                    "选择首发2_矩阵循生": {"enabled": True},
                    "矩阵循生": {
                        "action": "custom",
                        "custom_action": "ResetIdentify",
                        "custom_action_param": {"mode": "矩阵循生"},
                    },
                }
            )

        return CustomAction.RunResult(success=True)
