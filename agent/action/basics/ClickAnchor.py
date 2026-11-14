"""通用 Custom 动作：按基准点取识别框上的位置，再叠加 (x, y) 偏移后点击。

    "position": "right", "x": -6, "y": 3
    → 先取 (x+w, y+h//2)，再往左 6px、往下 3px

基准点：top_left / top / top_right / left / center / right /
        bottom_left / bottom / bottom_right（默认 center）
x 正=右、负=左；y 正=下、负=上。
"""

import json

from maa.context import Context
from maa.custom_action import CustomAction

from logger_component import LoggerComponent

logger = LoggerComponent(__name__).logger


class ClickAnchor(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        param = json.loads(argv.custom_action_param or "{}")
        x, y, w, h = argv.box.x, argv.box.y, argv.box.w, argv.box.h

        position = param.get("position", "center")
        if position == "top_left":
            px, py = x, y
        elif position == "top":
            px, py = x + w // 2, y
        elif position == "top_right":
            px, py = x + w, y
        elif position == "left":
            px, py = x, y + h // 2
        elif position == "center":
            px, py = x + w // 2, y + h // 2
        elif position == "right":
            px, py = x + w, y + h // 2
        elif position == "bottom_left":
            px, py = x, y + h
        elif position == "bottom":
            px, py = x + w // 2, y + h
        elif position == "bottom_right":
            px, py = x + w, y + h
        else:
            logger.error(f"ClickAnchor: unknown position {position!r}")
            return CustomAction.RunResult(success=False)

        dx, dy = int(param.get("x", 0)), int(param.get("y", 0))
        px += dx
        py += dy

        logger.debug(
            f"ClickAnchor: {position} ({x}, {y}, {w}, {h}) + ({dx}, {dy}) -> ({px}, {py})"
        )
        context.tasker.controller.post_click(px, py).wait()
        return CustomAction.RunResult(success=True)
