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
        action = CombatActions(context, role_name="骇影")

        action.lens_lock()
        if action.check_status("检查骇影2阶段"):
            print("二阶段")
            # 红球
            print("开始消红球")
            for _ in range(30):
                if action.check_status("检查骇影2阶段"):
                    action.ball_elimination_target(2)  # 消球
                    time.sleep(0.05)
                    action.ball_elimination_target(1)
                    time.sleep(0.05)
            time.sleep(0.1)
            action.auxiliary_machine()
            action.auto_qte("a")

            # 黄球
            print("开始消黄球")
            for _ in range(20):
                if action.check_status("检查骇影2阶段"):
                    action.attack()
                    time.sleep(0.05)
                    action.ball_elimination_target(1)
                    time.sleep(0.05)
            action.auxiliary_machine()
            action.auto_qte("a")

            # 蓝球
            print("开始消蓝球")
            action.long_press_attack(1000)
            for _ in range(10):
                if action.check_status("检查骇影2阶段"):
                    action.ball_elimination_target(1)
                    time.sleep(0.05)
                    action.attack()
                    time.sleep(0.05)

            action.auxiliary_machine()
            action.auto_qte("a")

        elif action.count_signal_balls() >= 9:
            print("一阶段")
            item = 0
            while not action.check_Skill_energy_bar() and item < 100:
                action.ball_elimination_target(2)  # 消球
                time.sleep(0.05)
                action.ball_elimination_target(1)
                time.sleep(0.05)
                action.attack()
                time.sleep(0.05)
                item += 1

            action.use_skill()
            time.sleep(0.5)
        else:
            print("一阶段信号球不足")
            item = 0

            while not action.check_status("检查骇影2阶段") and item < 100:
                action.attack()
                print(bool(action.check_status("检查骇影2阶段")))
                time.sleep(0.05)
                item += 1

        return CustomAction.RunResult(success=True)
