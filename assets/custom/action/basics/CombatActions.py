from maa.context import Context
from maa.custom_action import CustomAction


# 待优化
class CombatActions(CustomAction):
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

    @staticmethod
    def attack(context: Context):
        """攻击"""
        return lambda: context.tasker.controller.post_click(1197, 636).wait()

    @staticmethod
    def dodge(context: Context):
        """闪避"""
        return lambda: context.tasker.controller.post_click(1052, 633).wait()

    @staticmethod
    def use_skill(context: Context):
        """技能"""
        return lambda: context.tasker.controller.post_click(915, 626).wait()

    @staticmethod
    def ball_elimination(context: Context):
        """消球"""
        return lambda: context.tasker.controller.post_click(1215, 510).wait()

    @staticmethod
    def trigger_qte_first(context: Context):
        """触发QTE/换人"""
        return lambda: context.tasker.controller.post_click(1208, 154).wait()

    @staticmethod
    def trigger_qte_second(context: Context):
        """触发QTE/换人"""
        return lambda: context.tasker.controller.post_click(1208, 265).wait()
