from maa.context import Context
from maa.custom_action import CustomAction


# 待优化
class CombatActions(CustomAction):
    """通用战斗"""

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        try:
            self.ball_elimination(context)()
            self.use_skill(context)()
            self.attack(context)()

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
        return lambda: context.tasker.controller.post_click(
            1097, 510
        ).wait()  # 改成了消第二个球

    @staticmethod
    def trigger_qte_first(context: Context):
        """1-触发QTE/换人"""
        return lambda: context.tasker.controller.post_click(1208, 154).wait()

    @staticmethod
    def trigger_qte_second(context: Context):
        """2-触发QTE/换人"""
        return lambda: context.tasker.controller.post_click(1208, 265).wait()

    @staticmethod
    def long_press_attack(context: Context, time: int = 1200):
        """长按攻击"""
        return lambda: context.tasker.controller.post_swipe(
            1193, 633, 1198, 638, time
        ).wait()

    @staticmethod
    def long_press_dodge(context: Context, time: int):
        """长按闪避"""
        return lambda: context.tasker.controller.post_swipe(
            1052, 633, 1198, 638, time
        ).wait()

    @staticmethod
    def long_press_skill(context: Context, time: int):
        """长按技能"""
        return lambda: context.tasker.controller.post_swipe(
            915, 626, 915, 634, time
        ).wait()
