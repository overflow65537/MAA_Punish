from maa.context import Context
from maa.custom_action import CustomAction
import json
from agent.logger_component import LoggerComponent


logger_component = LoggerComponent(__name__)
logger = logger_component.logger


class ResetCount(CustomAction):
    """
    重置计数器。

    参数格式:
    {
        "nodes": [String], # 目标计数器节点名称列表
        "strict": bool # 可选，任一节点重置失败时 action 是否视为失败，默认 false
    }
    """

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:

        try:
            param = json.loads(argv.custom_action_param)
        except ValueError as e:
            logger.error(f"ResetCount: {e}")
            return CustomAction.RunResult(success=False)
        nodes = param.get("nodes", None)
        if not isinstance(nodes, list) or not nodes:
            logger.error("ResetCount requires non-empty custom_action_param.nodes")
            return CustomAction.RunResult(success=False)

        strict = param.get("strict", False)
        if not isinstance(strict, bool):
            logger.error("ResetCount requires boolean custom_action_param.strict")
            return CustomAction.RunResult(success=False)

        has_failure = False

        for index, node_name in enumerate(nodes):
            if not isinstance(node_name, str) or not node_name:
                log = logger.error if strict else logger.warning
                log(
                    f"ResetCount received invalid node name in custom_action_param.nodes[{index}]: {node_name!r}"
                )
                has_failure = True
                continue

            if not context.clear_hit_count(node_name):
                log = logger.error if strict else logger.warning
                log(
                    f"ResetCount failed to clear hit count: index={index}, node={node_name}"
                )
                has_failure = True
                continue

            #logger.info(f"ResetCount successfully cleared hit count: node={node_name}")

        if has_failure and strict:
            logger.error("ResetCount failed to clear some nodes in strict mode")
            return CustomAction.RunResult(success=False)

        return CustomAction.RunResult(success=True)
