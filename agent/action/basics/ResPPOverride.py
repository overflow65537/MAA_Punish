"""
MAA_Punish
MAA_Punish 资源级 pipeline 覆盖
作者:overflow65537
"""

from maa.context import Context
from maa.custom_action import CustomAction
import json


class PPOverride(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        param: dict = json.loads(argv.custom_action_param)
        if not param:
            return CustomAction.RunResult(success=True)
        context.tasker.resource.override_pipeline(param)
        return CustomAction.RunResult(success=True)
