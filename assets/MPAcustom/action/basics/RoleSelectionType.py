"""
MAA_Punish
MAA_Punish 选择特定类型角色
作者:overflow65537
"""

from maa.context import Context
from maa.custom_action import CustomAction
from maa.define import TemplateMatchResult, OCRResult, ColorMatchResult
import json

from MPAcustom.logger_component import LoggerComponent


class RoleSelectionType(CustomAction):
    def __init__(self):
        super().__init__()
        self._logger_component = LoggerComponent(__name__)
        self.logger = self._logger_component.logger

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:

        param = json.loads(argv.custom_action_param) or {}

        for _ in range(5):
            image = context.tasker.controller.post_screencap().wait().get()
            target_reco = context.run_recognition("检查支援类型角色", image)
            if target_reco and target_reco.hit:
                for reco in target_reco.filtered_results:
                    if not isinstance(reco, TemplateMatchResult):
                        continue
                    flag = context.run_recognition(
                        "检查支援类型角色是否被选中",
                        image,
                        {
                            "检查支援类型角色是否被选中": {
                                "recognition": {
                                    "param": {"roi": reco.box},
                                }
                            }
                        },
                    )
                    if param.get("cage"):
                        cage_reco = context.run_recognition(
                            "识别囚笼次数_辅助",
                            image,
                            {
                                "识别囚笼次数_辅助": {
                                    "recognition": {
                                        "param": {"roi": reco.box},
                                    }
                                }
                            },
                        )
                        if cage_reco and not cage_reco.hit:
                            continue

                    if flag and not flag.hit:
                        context.tasker.controller.post_click(
                            reco.box[0], reco.box[1]
                        ).wait()
                        context.run_task("编入队伍")
                        return CustomAction.RunResult(success=True)

            context.run_action("滑动_选人")

        context.run_task("返回")
        return CustomAction.RunResult(success=True)
