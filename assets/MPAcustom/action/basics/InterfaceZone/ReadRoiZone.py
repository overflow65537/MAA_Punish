"""
MAA_Punish
MAA_Punish 读取识别区
作者:overflow65537
"""

from pathlib import Path

from maa.context import Context
from maa.custom_action import CustomAction
import json


class ReadROIZone(CustomAction):
    _ZONES = (
        ("atk_zone", "识别攻击区", [1132, 572, 124, 123]),
        ("dodge_zone", "识别闪避区", [992, 571, 124, 124]),
        ("skill_zone", "识别大招区", [853, 571, 124, 126]),
        ("signal_zone", "识别信号球区", [414, 439, 853, 116]),
        ("corepass_zone", "识别核心被动区", [493, 602, 294, 50]),
        ("assist_zone", "识别辅助机区", [1168, 340, 92, 93]),
        ("lock_zone", "识别锁定区", [1070, 344, 81, 82]),
        ("switch_zone", "识别换人区", [1160, 110, 107, 231]),
    )

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        image = context.tasker.controller.post_screencap().wait().get()
        result: dict = {}

        for key, entry, default in self._ZONES:
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

        output_path = Path("roi_zone_offset.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

        return CustomAction.RunResult(success=True)
