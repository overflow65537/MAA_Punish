"""
MAA_Punish
MAA_Punish pipeline 兑换码程序
作者:overflow65537
"""


from maa.context import Context
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
import json
import time
from pathlib import Path

# 兑换码列表 / 填码动作所在的节点
CODE_NODE = "可以输入兑换码"
# 判断需不需要兑换的识别器节点
CHECK_NODE = "检查是否需要运行"


def load_redeemed_codes() -> list:
    """读取工作目录下已经兑换过的兑换码"""
    inv_code_path = Path("inv_code.json")
    if not inv_code_path.exists():
        return []
    with open("inv_code.json", "r") as f:
        data = json.load(f)
    if data is None:
        return []
    return data.get("inv_code", [])


def load_codes(context: Context) -> list | None:
    """读取节点上配置的兑换码列表，节点不存在时返回 None"""
    pipeline_obj = context.get_node_data(CODE_NODE)
    if pipeline_obj is None:
        return None
    return (
        pipeline_obj.get("action", {})
        .get("param", {})
        .get("custom_action_param", {})
        .get("code", [])
    )


class RedeemCode(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        codes = load_codes(context)
        if codes is None:
            self.send_msg(context, "兑换码节点不存在")
            return CustomAction.RunResult(success=False)

        # 读取工作目录下的兑换码文件
        inv_code = load_redeemed_codes()

        for code in codes:
            if code in inv_code:
                continue
            else:
                context.run_task("点击兑换码")
                time.sleep(0.1)
                print(code)

                self.send_msg(context, f"开始兑换 {code}")
                print(f"输入兑换码 {code}")
                context.tasker.controller.post_input_text(str(code))
                time.sleep(0.1)
                context.run_task("确认兑换")

                inv_code.append(code)
                with open("inv_code.json", "w") as f:
                    json.dump({"inv_code": inv_code}, f, indent=4)

                return CustomAction.RunResult(success=True)

        self.send_msg(context, "所有兑换码已兑换")
        # 全部兑换完，这次不去改入口节点「兑换码」的 next，
        # 而是改识别器节点自己的 next：本节点跑完后框架会回到它并重跑它的 next
        context.override_next(CHECK_NODE, ["返回主菜单"])
        return CustomAction.RunResult(success=True)

    def send_msg(self, context: Context, msg: str):
        msg_node = {
            "发送消息_这是程序自动生成的node所以故意写的很长来防止某一天想不开用了这个名字导致报错": {
                "focus": {"Node.Recognition.Succeeded": msg}
            }
        }
        context.run_task(
            "发送消息_这是程序自动生成的node所以故意写的很长来防止某一天想不开用了这个名字导致报错",
            pipeline_override=msg_node,
        )


class CheckRedeemCode(CustomRecognition):
    """判断还有没有要输入的兑换码

    命中 = 还有没兑换的码，由 next 走正常的兑换流程；
    未命中 = 没有要换的码，由 pipeline 里的空任务直接收尾。
    """

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult | None:
        codes = load_codes(context)
        if codes is None:
            print(f"{CODE_NODE} 节点不存在，跳过兑换")
            return None

        inv_code = load_redeemed_codes()
        for code in codes:
            if code in inv_code:
                continue
            print(f"兑换码 {code} 未兑换")
            # 只是用来决定要不要进兑换流程，不需要点击，box 给个空值就行
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 0, 0),
                detail={"status": "need_redeem", "code": code},
            )

        print("所有兑换码均已兑换")
        return None
