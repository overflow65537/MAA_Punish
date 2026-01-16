"""
MAA_Punish
MAA_Punish 选择特定类型角色
作者:overflow65537
"""

import re
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

        multi_member_config = context.get_node_data("多成员组队") or {}
        if not multi_member_config.get("enabled", False):
            context.run_task("返回")
            print("关闭多成员选择模式")
            self.send_msg(context, "关闭多成员选择模式")
            return CustomAction.RunResult(success=True)
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

    def send_msg(self, context: Context, msg: str):
        msg_node = {
            "发送消息_这是程序自动生成的node所以故意写的很长来防止某一天想不开用了这个名字导致报错": {
                "focus": {"Node.Recognition.Succeeded": msg}
            }
        }
        context.run_task(
            "发送消息_这是程序自动生成的node所以故意写的很长来防止某一天想不开用了这个名字导致报错",
            pipeline_override=msg_node,
        )
