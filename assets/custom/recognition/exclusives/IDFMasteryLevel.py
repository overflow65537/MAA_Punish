from maa.context import Context
from maa.custom_recognition import CustomRecognition


class IDFMasteryLevel(CustomRecognition):

    def analyze(
        self,
        context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        result = context.run_recognition(
            "选择自动作战人物_矩阵循生",
            argv.image,
            {
                "选择自动作战人物_矩阵循生": {
                    "template": [
                        "肉鸽通用\\誓焰终解_矩阵.png",
                        "肉鸽通用\\誓焰_矩阵.png",
                        "肉鸽通用\\誓焰花嫁_矩阵.png",
                        "肉鸽通用\\深红囚影终解_矩阵.png",
                        "肉鸽通用\\深红囚影_矩阵.png",
                        "肉鸽通用\\深谣终解_矩阵.png",
                        "肉鸽通用\\深谣_矩阵.png",
                        "肉鸽通用\\终焉终解_矩阵.png",
                        "肉鸽通用\\终焉_矩阵.png",
                        "肉鸽通用\\深痕终解_矩阵.png",
                        "肉鸽通用\\深痕_矩阵.png",

                    ],
                    "threshold": [0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9],
                }
            },
        )
        if result:
            for i in result.filterd_results:
                if context.run_recognition(
                    "识别精通等级",
                    argv.image,
                    {
                        "识别精通等级": {
                            "roi": i.box,
                            "roi_offset": [189, 25, -51, -45],
                        }
                    },
                ):
                    context.override_pipeline(
                        {
                            "战斗事件_矩阵循生": {
                                "interrupt": [
                                    "识别人物",
                                    "重启_寒境曙光",
                                    "战斗中",
                                    "出击_矩阵循生",
                                    "跳过战斗对话_寒境曙光",
                                    "进入战斗_矩阵循生",
                                    "载入中",
                                ]
                            },
                            "识别人物": {"enabled": True},
                        }
                    )
                    print("IDFMasteryLevel success")
                    return CustomRecognition.AnalyzeResult(box=i.box, detail="success")
        print("IDFMasteryLevel failed")
        return
