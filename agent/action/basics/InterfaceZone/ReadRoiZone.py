"""
MAA_Punish
在布局界面读取各识别区并写入偏移缓存
作者:overflow65537
"""

from maa.context import Context
import json

from action.basics.InterfaceZone.roi_zone_controller import (
    offset_path,
    zones_for,
)


def capture_roi_zones(context: Context, controller: str) -> bool:
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
            _send_msg(context, f"{key} 读取失败")
            failed = True

    if failed:
        _send_msg(context, "读取ROI偏移配置失败,请切换键位为新界面")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

    print(f"capture_roi_zones controller={controller} saved to {output_path}")
    return not failed


def _send_msg(context: Context, msg: str):
    msg_node = {
        "发送消息_这是程序自动生成的node所以故意写的很长来防止某一天想不开用了这个名字导致报错": {
            "focus": {"Node.Recognition.Succeeded": msg}
        }
    }
    context.run_task(
        "发送消息_这是程序自动生成的node所以故意写的很长来防止某一天想不开用了这个名字导致报错",
        pipeline_override=msg_node,
    )
