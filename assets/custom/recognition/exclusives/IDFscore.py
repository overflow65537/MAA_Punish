from maa.context import Context
from maa.custom_recognition import CustomRecognition


class IDFscore(CustomRecognition):

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
        if current_score is None or target_score is None:
            return
        if current_score.best_result.text.isdigit() and target_score.best_result.text.isdigit():
            
            if int(current_score.best_result.text) >= int(target_score.best_result.text):
                return CustomRecognition.AnalyzeResult(
                    box=(0, 0, 100, 100), detail=f"{current_score.best_result.text}>={target_score.best_result.text}"
                )
        else:
            return
