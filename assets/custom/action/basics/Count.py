# Copyright (c) 2024-2025 MAA_Punish
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
MAA_Punish
MAA_Punish 计数程序
作者:overflow65537
"""

from maa.context import Context
from maa.custom_action import CustomAction
import json


class Count(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        """
        自定义动作：
        custom_action_param:
            {
                "count": 0,
                "target_count": 10,
                "next_node": ["node1", "node2"],
                "else_node": ["node3"],
                "next_node_msg": "已达到目标次数，执行下一节点 {next_node}",
                "else_node_msg": "未达到目标次数，执行备用节点 {else_node}",
                "count_msg": "当前次数: {count}, 目标次数: {target_count}"
            }
        count: 当前次数
        target_count: 目标次数
        next_node: 达到目标次数后执行的节点. 支持多个节点，按顺序执行，可以出现重复节点，可以为空
        else_node: 未达到目标次数时执行的节点. 支持多个节点，按顺序执行，可以出现重复节点，可以为空
        next_node_msg: 达到目标次数后执行的节点时的提示消息，可以为空 可以使用 {next_node} 来引用 next_node 中的节点名称
        else_node_msg: 未达到目标次数时执行的节点时的提示消息 可以为空 可以使用 {else_node} 来引用 else_node 中的节点名称
        count_msg: 每次执行时的提示消息 可以为空 可以使用 {count} 来引用 count 中的当前次数 可以使用 {target_count} 来引用 target_count 中的目标次数
        """

        argv_dict: dict = json.loads(argv.custom_action_param)
        if not argv_dict:
            return CustomAction.RunResult(success=True)

        # 提取参数
        current_count: int = argv_dict.get("count", 0)
        target_count: int = argv_dict.get("target_count", 0)
        next_node_msg: str = argv_dict.get("next_node_msg", "")
        else_node_msg: str = argv_dict.get("else_node_msg", "")
        count_msg: str = argv_dict.get("count_msg", "")

        if current_count <= target_count:
            # 计数未达标时：递增计数并执行备用节点
            new_count = current_count + 1
            argv_dict["count"] = new_count

            # 输出计数提示（使用更新后的计数）
            if count_msg:
                self.custom_notify(
                    context,
                    count_msg.format(count=new_count - 1, target_count=target_count),
                )

            # 保存更新后的参数
            context.override_pipeline(
                {argv.node_name: {"custom_action_param": argv_dict}}
            )

            # 输出备用节点提示
            else_nodes = argv_dict.get("else_node")
            if else_node_msg and else_nodes:
                node_str = (
                    else_nodes if isinstance(else_nodes, str) else ", ".join(else_nodes)
                )
                self.custom_notify(context, else_node_msg.format(else_node=node_str))
            self._run_nodes(context, else_nodes)
        else:
            # 计数达标时：重置计数并执行下一节点
            reset_params = {
                "count": 0,
                "target_count": target_count,
                "else_node": argv_dict.get("else_node"),
                "next_node": argv_dict.get("next_node"),
                # 保留消息参数避免丢失
                "next_node_msg": next_node_msg,
                "else_node_msg": else_node_msg,
                "count_msg": count_msg,
            }

            # 保存重置后的参数
            context.override_pipeline(
                {argv.node_name: {"custom_action_param": reset_params}}
            )

            # 输出下一节点提示
            next_nodes = argv_dict.get("next_node")
            if next_node_msg and next_nodes:
                node_str = (
                    next_nodes if isinstance(next_nodes, str) else ", ".join(next_nodes)
                )
                self.custom_notify(context, next_node_msg.format(next_node=node_str))
            self._run_nodes(context, next_nodes)

        return CustomAction.RunResult(success=True)

    def _run_nodes(self, context: Context, nodes: str | list[str] | None):
        """统一处理节点执行逻辑"""
        if not nodes:
            return
        # 确保节点列表为列表类型
        if isinstance(nodes, str):
            nodes = [nodes]
        for node in nodes:
            context.run_task(node)

    def custom_notify(self, context: Context, msg):
        context.override_pipeline({"custom通知": {"focus": {"succeeded": msg}}})
        context.run_task("custom通知")
