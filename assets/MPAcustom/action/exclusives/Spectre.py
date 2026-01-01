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
                if actions.check_status("检查骇影2阶段"):
                    actions.ball_elimination_target(2)  # 消球
                    time.sleep(0.05)
                    actions.ball_elimination_target(1)
                    time.sleep(0.05)
            time.sleep(0.1)

            # 黄球
            print("开始消黄球")
            for _ in range(20):
                if actions.check_status("检查骇影2阶段"):
                    actions.attack()
                    time.sleep(0.05)
                    actions.ball_elimination_target(1)
                    time.sleep(0.05)

            # 蓝球
            print("开始消蓝球")
            actions.long_press_attack(1000)
            for _ in range(10):
                if actions.check_status("检查骇影2阶段"):
                    actions.ball_elimination_target(1)
                    time.sleep(0.05)
                    actions.attack()
                    time.sleep(0.05)

        elif actions.count_signal_balls() >= 9:
            print("一阶段")
            item = 0
            while not actions.check_Skill_energy_bar() and item < 100:
                actions.ball_elimination_target(2)  # 消球
                time.sleep(0.05)
                actions.ball_elimination_target(1)
                time.sleep(0.05)
                actions.attack()
                time.sleep(0.05)
                item += 1

            actions.use_skill()
            time.sleep(0.5)
        else:
            print("一阶段信号球不足")
            item = 0

            while not actions.check_status("检查骇影2阶段") and item < 100:
                actions.attack()
                print(bool(actions.check_status("检查骇影2阶段")))
                time.sleep(0.05)
                item += 1

        return CustomAction.RunResult(success=True)
