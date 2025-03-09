from maa.context import Context
from maa.custom_action import CustomAction


class SetTower(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        image = context.tasker.controller.post_screencap().wait().get()
        target_pos = context.run_recognition("战斗地块_寒境曙光", image)
        if target_pos:
            image = context.tasker.controller.post_screencap().wait().get()
            empty_pos = context.run_recognition(
                "识别周围空地",
                image,
                {
                    "识别周围空地": {
                        "roi": "战斗地块_寒境曙光",
                        "roi_offset": [-240, -180, 380, 320],
                    }
                },
            )
            if empty_pos:
                context.tasker.controller.post_click(
                    empty_pos.best_result.box[0], empty_pos.best_result.box[1]
                ).wait()
        return CustomAction.RunResult(success=True)
