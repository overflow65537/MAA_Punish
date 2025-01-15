from maa.context import Context
from maa.custom_action import CustomAction

class Identify(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        image = context.tasker.controller.post_screencap().wait().get()
        if context.run_recognition("检查终焉", image) :
            context.override_next("战斗中", ["终焉战斗"])
            context.override_pipeline("识别人物",{"enabled": False} )
        elif context.run_recognition("检查深痕", image) :
            context.override_next("战斗中", ["深痕战斗"])
            context.override_pipeline("识别人物",{"enabled": False} )
        elif context.run_recognition("检查深谣", image) :
            context.override_next("战斗中", ["深谣战斗"])
            context.override_pipeline("识别人物",{"enabled": False} )
        elif context.run_recognition("检查深红囚影", image) :
            context.override_next("战斗中", ["深红囚影"])
            context.override_pipeline("识别人物",{"enabled": False} )
        elif context.run_recognition("检查誓焰", image) :
            context.override_next("战斗中", ["誓焰战斗"])
            context.override_pipeline("识别人物",{"enabled": False} )
        return CustomAction.RunResult(success=True)
