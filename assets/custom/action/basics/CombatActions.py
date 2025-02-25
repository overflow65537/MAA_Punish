import time

from maa.context import Context
from maa.custom_action import CustomAction

# 待优化
class CombatActions(CustomAction):
    # def __init__(self):
    #     """初始化"""
    #     self.name = "CombatActions"

    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        try:
            context.tasker.controller.post_click(1215, 510).wait()
            context.tasker.controller.post_click(1197, 636).wait()
            context.tasker.controller.post_click(1215, 510).wait()
            context.tasker.controller.post_click(915, 626).wait()
            context.tasker.controller.post_click(1208, 154).wait()
            context.tasker.controller.post_click(1197, 636).wait()
            context.tasker.controller.post_click(1208, 265).wait()
            
            return CustomAction.RunResult(success=True)
        except Exception as e:
            return CustomAction.RunResult(success=False)

    # def attack(self, context: Context):
    #     """攻击"""
    #     attack_job = context.tasker.controller.post_click(1197, 636).wait()

    # def dodge(self, context: Context):
    #     """闪避"""
    #     dodge_job = context.tasker.controller.post_click(1052, 633).wait()

    # def use_skill(self, context: Context):
    #     """技能"""
    #     skill_job = context.tasker.controller.post_click(915, 626).wait()

    # def consume_resource(self, context: Context):
    #     """消球"""
    #     consume_job = context.tasker.controller.post_click(1215, 510).wait()

    # def trigger_qte(self, context: Context):
    #     """触发QTE"""
    #     qte_job_1 = context.tasker.controller.post_click(1208, 154).wait()
    #     time.sleep(0.1)
    #     qte_job_2 = context.tasker.controller.post_click(1208, 265).wait()
