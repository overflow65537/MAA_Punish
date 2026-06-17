"""
MAA_Punish
MAA_Punish 通知
作者:overflow65537
"""

from maa.context import Context
from maa.custom_action import CustomAction
from maa.define import OCRResult
import json
import datetime


class Notice(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        param: dict = json.loads(argv.custom_action_param)
        action = param.get("action")
        if action == "set_black_card":
            image = context.tasker.controller.post_screencap().wait().get()
            black_card_reco = context.run_recognition("识别黑卡", image)
            if (
                black_card_reco
                and black_card_reco.hit
                and isinstance(black_card_reco.best_result, OCRResult)
            ):
                black_card = black_card_reco.best_result.text

            else:
                black_card = "0"

            context.tasker.resource.override_pipeline(
                {"资源变量": {"focus": {"start_black_card": black_card}}}
            )
        elif action == "show_black_card":
            image = context.tasker.controller.post_screencap().wait().get()
            end_black_card_reco = context.run_recognition("识别黑卡", image)

            if (
                end_black_card_reco
                and end_black_card_reco.hit
                and isinstance(end_black_card_reco.best_result, OCRResult)
            ):
                end_black_card = end_black_card_reco.best_result.text
            else:
                end_black_card = "0"

            energy_reco = context.run_recognition("识别体力", image)

            if (
                energy_reco
                and energy_reco.hit
                and isinstance(energy_reco.best_result, OCRResult)
            ):
                energy = energy_reco.best_result.text
            else:
                energy = "0"

            resource = context.get_node_object("资源变量")
            if resource is None:
                return CustomAction.RunResult(success=True)
            start_black_card = resource.focus.get("start_black_card")

            # 收益
            if (
                start_black_card.isdigit()
                and end_black_card.isdigit()
                and energy.isdigit()
            ):
                profit = int(end_black_card) - int(start_black_card)
                next_energy = 240 - int(energy) * 6 * 60

                now_time = datetime.datetime.now()
                next_time = now_time + datetime.timedelta(seconds=next_energy)
                self.custom_notify(context, "初始黑卡:")
                self.custom_notify(context, start_black_card)
                self.custom_notify(context, "当前黑卡:")
                self.custom_notify(context, end_black_card)
                self.custom_notify(context, "收益:")
                self.custom_notify(context, str(profit))

                self.custom_notify(context, "下次体力恢复时间:")
                self.custom_notify(context, next_time.strftime("%Y-%m-%d %H:%M:%S"))

        return CustomAction.RunResult(success=True)

    def custom_notify(self, context: Context, msg: str):
        """自定义通知"""
        context.override_pipeline(
            {"custom通知": {"focus": {"Node.Recognition.Succeeded": msg}}}
        )
        context.run_task("custom通知")
