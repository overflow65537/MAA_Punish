import logging
from maa.context import Context
from maa.custom_action import CustomAction


class CombatActions(CustomAction):
    """通用战斗"""

    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        print("通用战斗")
        try:
            self.lens_lock(context)()
            self.ball_elimination_second(context)()
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
        return lambda: context.tasker.controller.post_click(1216, 518).wait()# 消第一个球
    
    @staticmethod
    def ball_elimination_second(context: Context):
        """消球2"""
        return lambda: context.tasker.controller.post_click(1097, 510).wait()  # 消第二个球
    
    @staticmethod
    def ball_elimination_three(context: Context):
        """消球3"""
        return lambda: context.tasker.controller.post_click(999, 518).wait()  # 消第三个球

    @staticmethod
    def trigger_qte_first(context: Context):
        """1-触发QTE/换人"""
        return lambda: context.tasker.controller.post_click(1208, 154).wait()

    @staticmethod
    def trigger_qte_second(context: Context):
        """2-触发QTE/换人"""
        return lambda: context.tasker.controller.post_click(1208, 265).wait()

    @staticmethod
    def long_press_attack(context: Context, time: int = 1000):
        """长按攻击"""
        return lambda: context.tasker.controller.post_swipe(1193, 633, 1198, 638, time).wait()

    @staticmethod
    def long_press_dodge(context: Context, time: int = 1000):
        """长按闪避"""
        return lambda: context.tasker.controller.post_swipe(1052, 633, 1198, 638, time).wait()

    @staticmethod
    def long_press_skill(context: Context, time: int = 1000):
        """长按技能"""
        return lambda: context.tasker.controller.post_swipe(915, 626, 915, 634, time).wait()

    @staticmethod
    def lens_lock(context: Context):
        """镜头锁定"""
        return lambda: context.tasker.controller.post_click(1108, 383).wait()

    @staticmethod
    def auxiliary_machine(context: Context):
        """辅助机"""
        return lambda: context.tasker.controller.post_click(1214, 387).wait()

    @staticmethod
    def check_status(context: Context, node: str,role_name:str) -> bool:
        """检查状态"""
        try:
            logger = logging.getLogger(f"{role_name}_Job")
            # 获取截图
            image = context.tasker.controller.post_screencap().wait().get()
            # 识别并返回结果
            if context.run_recognition(node, image):
                logger.info(node +":True")
                return True
            else:
                logger.info(node +":False")
                return False
        except Exception as e:
            logger.exception(node+":"+str(e))
            return False
    
    @staticmethod
    def check_Skill_energy_bar(context: Context,role_name:str) -> bool:
        """检查技能能量条"""
        try:
            logger = logging.getLogger(f"{role_name}_Job")
            # 获取截图
            image = context.tasker.controller.post_screencap().wait().get()
            # 识别并返回结果
            if context.run_recognition("技能_能量条", image):
                logger.info("检查技能_能量条:True")
                return True
            else:
                logger.info("检查技能_能量条:False")
                return False
        except Exception as e:
            logger.exception("检查技能_能量条:"+str(e))
            return False

