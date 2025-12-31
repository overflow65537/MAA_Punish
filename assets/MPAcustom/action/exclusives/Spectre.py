"""
MAA_Punish
MAA_Punish 骇影战斗程序
作者:overflow65537
"""

import time
from MPAcustom.action.basics import CombatActions
from maa.context import Context
from maa.custom_action import CustomAction


class Spectre(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        actions = CombatActions(context, role_name="骇影")

        actions.lens_lock()
        if actions.check_status("检查骇影2阶段"):
            print("二阶段")
            # 红球
            print("开始消红球")
            for _ in range(30):
                actions.ball_elimination_target(2)  # 消球
                time.sleep(0.05)
                actions.ball_elimination_target(1)
                time.sleep(0.05)
                actions.auto_qte("r")
            time.sleep(0.1)

            # 黄球
            print("开始消黄球")
            for _ in range(20):
                actions.attack()
                time.sleep(0.05)
                actions.ball_elimination_target(1)
                time.sleep(0.05)

            # 蓝球
            print("开始消蓝球")
            actions.long_press_attack(1000)
            for _ in range(10):
                actions.ball_elimination_target(1)
                time.sleep(0.05)
                actions.attack()
                time.sleep(0.05)

        elif actions.count_signal_balls() >= 9:
            print("一阶段")
            for _ in range(20):
                actions.ball_elimination_target(2)  # 消球
                time.sleep(0.05)
                actions.ball_elimination_target(1)
                time.sleep(0.05)
                actions.attack()
                time.sleep(0.05)

            if actions.check_Skill_energy_bar():
                actions.use_skill()
                time.sleep(0.5)
        else:
            print("一阶段信号球不足")
            actions.continuous_attack(8, 100)

        return CustomAction.RunResult(success=True)
