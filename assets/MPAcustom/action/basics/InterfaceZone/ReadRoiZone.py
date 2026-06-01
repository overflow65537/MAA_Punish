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

        for key, entry, default in zones:
            reco = context.run_recognition(entry, image)
            if reco and reco.hit and reco.best_result:
                recognized = list(reco.best_result.box)
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
                print(f"{key} recognition failed")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

        print(f"ReadROIZone controller={controller} saved to {output_path}")
        return CustomAction.RunResult(success=True)
