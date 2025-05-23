from maa.context import Context
from maa.custom_recognition import CustomRecognition
import json


class LOp(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        """
        逻辑识别器：
        custom_recognition_param:
            {
                "mode": and,
                "nodes": ["node1", ["node2"]],
            }
        mode: 模式 and 或者 or,默认为and
        nodes: 需要识别的节点,使用列表括起来为反转识别结果
        """
        image = argv.image
        param: dict = json.loads(argv.custom_recognition_param)
        mode: str = param.get("mode", "and")
        nodes: list = param.get("nodes", [])

        if mode == "and":
            for item in nodes:
                result = self._eval_node(item, context, image)
                if not result:
                    return
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100), detail=f"{nodes} used in {mode} success"
            )

        elif mode == "or":
            for item in nodes:
                result = self._eval_node(item, context, image)
                if result:
                    return CustomRecognition.AnalyzeResult(
                        box=(0, 0, 100, 100), detail=f"{nodes} used in {mode} success"
                    )
            return

        else:
            return

    def _eval_node(self, node, context: Context, image):

        if isinstance(node, str):
            return context.run_recognition(node, image)

        elif isinstance(node, list) and len(node) == 1:
            inner_node = node[0]
            return not context.run_recognition(inner_node, image)
