"""
MAA_Punish
MAA_Punish 读取识别区
作者:overflow65537
"""

from maa.context import Context
from maa.custom_action import CustomAction
import json

from action.basics.InterfaceZone.roi_zone_controller import (
    offset_path,
    parse_controller,
    parse_param,
    zones_for,
)


class ReadROIZone(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        controller = parse_controller(parse_param(argv.custom_action_param))
        zones = zones_for(controller)
        output_path = offset_path(controller)

        image = context.tasker.controller.post_screencap().wait().get()
        result: dict = {}
        failed = False

        for key, entry, default in zones:
            reco = context.run_recognition(entry, image)
            if reco and reco.hit and reco.box:
                recognized = list(reco.box)
                offset = [recognized[i] - default[i] for i in range(4)]
                result[key] = {
                    "default": default,
                    "recognized": recognized,
                    "offset": offset,
                    "hit": True,
                }
                print(f"{key} recognized={recognized} offset={offset}")
            else:
                result[key] = {
                    "default": default,
                    "recognized": None,
                    "offset": None,
                    "hit": False,
                }
                self.send_msg(context, f"{key} 读取失败")
                failed = True

        if failed:
            self.send_msg(context, "读取ROI偏移配置失败,请切换键位为新界面")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

        print(f"ReadROIZone controller={controller} saved to {output_path}")
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