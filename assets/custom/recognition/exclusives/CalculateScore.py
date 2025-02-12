from maa.context import Context
from maa.custom_recognition import CustomRecognition


class CalculateScore(CustomRecognition):

    def analyze(
        self,
        context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        image = context.tasker.controller.post_screencap().wait().get()
        # 检查目标分数
        target_score = context.run_recognition("检查目标分数", image)
        # 检查当前分数
        current_score = context.run_recognition("检查当前分数", image)

        # 检查军事分数及倍率
        military_score = context.run_recognition(
            "检查分数", image, {"检查分数": {"roi": [90, 238, 105, 44]}}
        )
        military_multiplier = context.run_recognition(
            "检查分数", image, {"检查分数": {"roi": [197, 239, 54, 48], "expected": ""}}
        )

        # 检查经济分数及倍率
        economic_score = context.run_recognition(
            "检查分数", image, {"检查分数": {"roi": [90, 327, 105, 44]}}
        )
        economic_multiplier = context.run_recognition(
            "检查分数", image, {"检查分数": {"roi": [193, 323, 61, 52], "expected": ""}}
        )

        # 检查科研分数及倍率
        research_score = context.run_recognition(
            "检查分数", image, {"检查分数": {"roi": [90, 412, 107, 46]}}
        )
        research_multiplier = context.run_recognition(
            "检查分数", image, {"检查分数": {"roi": [196, 416, 61, 43], "expected": ""}}
        )

        if None in [
            current_score,
            target_score,
            military_score,
            military_multiplier,
            economic_score,
            economic_multiplier,
            research_score,
            research_multiplier,
        ]:
            return

        if (
            current_score.best_result.text.isdigit()
            and target_score.best_result.text.isdigit()
            and military_score.best_result.text.isdigit()
            and military_multiplier.best_result.text[1:].isdigit()
            and economic_score.best_result.text.isdigit()
            and economic_multiplier.best_result.text[1:].isdigit()
            and research_score.best_result.text.isdigit()
            and research_multiplier.best_result.text[1:].isdigit()
        ):
            final_score = (
                int(military_score.best_result.text)
                * int(military_multiplier.best_result.text[1:])
                + int(economic_score.best_result.text)
                * int(economic_multiplier.best_result.text[1:])
                + int(research_score.best_result.text)
                * int(research_multiplier.best_result.text[1:])
                + int(current_score.best_result.text)
            )
            print(final_score)
            if final_score >= int(target_score.best_result.text):
                return CustomRecognition.AnalyzeResult(
                    box=(0, 0, 100, 100), detail="success"
                )
        else:
            return
