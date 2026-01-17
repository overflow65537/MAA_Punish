"""
MAA_Punish
MAA_Punish 希声战斗程序
作者:overflow65537
"""

import time
from MPAcustom.action.basics import CombatActions
from maa.context import Context
from maa.custom_action import CustomAction


class Pianissimo(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        action = CombatActions(context, role_name="希声")

        action.lens_lock()
        action.attack()
        if action.check_status("检查希声2阶段"):
            print("希声2阶段")
            start_time = time.time()

            while action.count_signal_balls() and time.time() - start_time < 10:
                if action.check_status("检查希声红球"):
                    action.use_skill()
                    return CustomAction.RunResult(success=True)
                action.ball_elimination_target(2)
                time.sleep(0.05)
                action.attack()
                time.sleep(0.03)

            print("希声2阶段消球结束")

            action.long_press_attack(1000)
            action.auto_qte("a")
            for _ in range(20):
                action.attack()
                time.sleep(0.05)
                action.ball_elimination_target(1)
                time.sleep(0.05)
            print("希声2阶段核心结束")

            start_time = time.time()
            while action.count_signal_balls() and time.time() - start_time < 10:
                if action.check_status("检查希声红球"):
                    action.use_skill()
                    time.sleep(0.2)
                    action.auxiliary_machine()
                    action.auto_qte("a")
                    action.switch()
                    print("切换完成")
                    return CustomAction.RunResult(success=True)
                action.ball_elimination_target(2)
                time.sleep(0.05)
                action.attack()
                time.sleep(0.03)

            action.long_press_dodge(700)
            action.auxiliary_machine()
            action.auto_qte("a")

            for _ in range(5):
                time.sleep(0.05)
                action.use_skill()
                action.auxiliary_machine()
                action.auto_qte("a")
                action.switch()
                print("切换完成")
                return CustomAction.RunResult(success=True)

        elif action.count_signal_balls() > 5:
            print("希声1阶段")
            start_time = time.time()
            while action.count_signal_balls() and time.time() - start_time < 10:
                if action.check_status("检查希声2阶段"):
                    return CustomAction.RunResult(success=True)
                action.attack()
                target = action.Arrange_Signal_Balls()
                action.attack()
                if target == -1:
                    target = -2
                action.ball_elimination_target(target)
                time.sleep(0.05)
                print(target)
                action.attack()
                time.sleep(0.05)
            print("希声1阶段消球结束")

            action.long_press_attack(1000)
            time.sleep(0.01)
            action.auto_qte("a")
            action.auxiliary_machine()
            for _ in range(15):
                action.attack()
                time.sleep(0.05)
                action.ball_elimination_target(1)
                time.sleep(0.05)
                action.use_skill()
        else:
            print("希声1阶段信号球不足")
            for _ in range(30):
                start_time = time.time()
                if (
                    action.check_status("检查希声2阶段")
                    or action.count_signal_balls() > 5
                    or context.tasker.stopping
                ):
                    break
                action.attack()
                end_time = time.time()
                elapsed_ms = (end_time - start_time) * 1000
                # 需要等待的时间（如果已用时间不足50ms）
                wait_ms = max(0, 50 - elapsed_ms)
                if wait_ms > 0:
                    time.sleep(wait_ms / 1000)
        action.attack()
        return CustomAction.RunResult(success=True)
