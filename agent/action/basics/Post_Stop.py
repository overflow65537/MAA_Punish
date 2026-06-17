from maa.context import Context
from maa.custom_action import CustomAction
import json


class PostStop(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        context.tasker.post_stop()
        return CustomAction.RunResult(success=True)
