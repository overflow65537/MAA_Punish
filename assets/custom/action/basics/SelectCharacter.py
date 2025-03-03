from maa.context import Context
from maa.custom_action import CustomAction
from maa.define import RecognitionDetail
import json
import time
import numpy


class SelectCharacter(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        param = json.loads(argv.custom_action_param)
        context.run_task("点击首发")
        image = context.tasker.controller.post_screencap().wait().get()
        print(param["target"])
        match param["target"]:
            case "nihil":  # 空
                return self.select_character(
                    context, image, "选择角色", ["肉鸽通用\\终焉.png"], 6
                )
            case "physical":  # 物理
                return self.select_character(
                    context, image, "选择角色", ["肉鸽通用\\深痕.png"], 6
                )
            case "dark":  # 暗
                return self.select_character(
                    context, image, "选择角色", ["肉鸽通用\\深谣.png"], 6
                )
            case "lightning":  # 雷
                return self.select_character(
                    context, image, "选择角色", ["肉鸽通用\\深红囚影.png"], 6
                )
            case "fire":  # 火
                return self.select_character(
                    context, image, "选择角色", ["肉鸽通用\\誓焰.png"], 6
                )
            case "ice":  # 冰
                return self.select_character(
                    context,
                    image,
                    "选择角色",
                    [
                        "肉鸽通用\\深红囚影.png",
                        "肉鸽通用\\誓焰.png",
                        "肉鸽通用\\深痕.png",
                        "肉鸽通用\\终焉.png",
                        "肉鸽通用\\深谣.png",
                    ],
                    6,
                )
            case _:
                return CustomAction.RunResult(success=False)

    def select_character(
        self,
        context: Context,
        image: numpy.ndarray,
        recognition_name,
        template,
        max_attempts,
    ):
        print(f"选择{recognition_name}")
        character = context.run_recognition(
            recognition_name, image, {recognition_name: {"template": template}}
        )
        run_times = 0
        while not character and run_times < max_attempts:
            run_times += 1
            self.perform_swipe(context)
            image = context.tasker.controller.post_screencap().wait().get()
            character = context.run_recognition(
                recognition_name, image, {recognition_name: {"template": template}}
            )

        if character:
            character_power = context.run_recognition("检查战力", image)
            if character_power:
                self.click_character(context, character_power)
                self.run_task_and_return(context)
                return CustomAction.RunResult(success=True)

        self.scroll_to_top(context)
        image = context.tasker.controller.post_screencap().wait().get()
        character = context.run_recognition("选择自动作战人物", image)
        run_times = 0
        while not character and run_times < 5:
            run_times += 1
            self.perform_swipe(context)
            image = context.tasker.controller.post_screencap().wait().get()
            character = context.run_recognition("选择自动作战人物", image)

        if character:
            self.click_character(context, character)
            self.run_task_and_return(context)
            return CustomAction.RunResult(success=True)

        self.scroll_to_top(context)
        context.tasker.controller.post_click(134, 116).wait()
        self.run_task_and_return(context)
        return CustomAction.RunResult(success=True)

    def perform_swipe(self, context: Context):
        context.tasker.controller.post_swipe(160, 600, 160, 150, 1000).wait()
        time.sleep(1)
        context.tasker.controller.post_click(160, 200).wait()
        time.sleep(0.5)

    def scroll_to_top(self, context: Context):
        for _ in range(4):
            context.tasker.controller.post_swipe(160, 100, 160, 600, 100).wait()
            time.sleep(0.5)

    def click_character(self, context: Context, character:RecognitionDetail):
        context.tasker.controller.post_click(
            character.best_result.box[0], character.best_result.box[1]
        ).wait()

    def run_task_and_return(self, context: Context):
        context.run_task(
            "编入队伍", {"作战开始": {"post_delay": 500, "action": "DoNothing","next": "自动战斗任务"}}
        )
