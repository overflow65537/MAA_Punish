"""
MAA_Punish
MAA_Punish 逆冕战斗程序
作者:overflow65537
"""

import time


from maa.context import Context
from maa.custom_action import CustomAction
from agent.action.basics import CombatActions


class InverseCrown(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        self.action = CombatActions(context, role_name="露西亚·逆冕")
        self.action.lens_lock()
        self.action.attack()
        if self.action.check_status("检查逆冕能量即将满"):
            self.action.logger.info("大招")
            self.skill_use(context)

        elif self.action.count_signal_balls() >= 16:
            self.action.logger.info("球数满足条件，进行球消")
            self.action.ball_elimination_target()

        elif self.action.count_signal_balls() > 7 and self.action.check_status(
            "检查逆冕特殊球"
        ):
            self.action.logger.info("特殊球就绪")
            context.run_action(
                "长按1号球", pipeline_override={"长按1号球": {"duration": 5500}}
            )
            self.action.logger.info("特殊球按下完成")
            atk_start_time = time.time()
            while (
                not self.action.check_status("检查逆冕能量即将满")
                and time.time() - atk_start_time < 5
            ):
                self.action.attack()
                time.sleep(0.05)

            self.skill_use(context)

        else:
            self.action.logger.info("特殊球未就绪")
            # action.long_press_attack(500)
            # time.sleep(0.05)
            for _ in range(20):
                self.action.attack()
                start_time = time.time()
                if self.action.check_status("检查逆冕特殊球"):
                    self.action.logger.info("特殊球就绪")
                    break
                else:
                    elapsed = time.time() - start_time
                    if elapsed < 0.05:
                        time.sleep(0.05 - elapsed)

        return CustomAction.RunResult(success=True)

    def skill_use(self, context: Context):
        cage = context.get_node_data("选择角色程序")
        if cage is None:
            cage = False
        else:
            cage = cage.get("attach", {}).get("cage", False)
        self.action.logger.info(f"cage: {cage}")

        if cage:
            self.action.long_press_skill(2000)
        else:
            skill_start_time = time.time()

            while (
                not self.action.check_status("检查逆冕能量即将满")
                and time.time() - skill_start_time < 10
            ):
                self.action.attack()
                time.sleep(0.05)
            for _ in range(20):
                self.action.use_skill()
                if self.action.check_status("检查逆冕能量空"):
                    break
                time.sleep(0.05)

            self.action.long_press_attack(4000)
