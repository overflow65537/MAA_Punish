from maa.context import Context
from maa.custom_action import CustomAction


class ResetIdentify(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        context.override_pipeline({"识别人物": {"enabled": True}})
        return CustomAction.RunResult(success=True)
