from maa.context import Context
from maa.custom_action import CustomAction
import time


class CrimsonWeave(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        image = context.tasker.controller.post_screencap().wait().get()
        if context.run_recognition("检查短刀_囚影", image):
            if context.run_recognition("检查u1_囚影", image):  # 检查一段大招
                context.tasker.controller.post_click(910, 631).wait() # 崩落的束缚化为利刃
                return CustomAction.RunResult(success=True)
            print("短刀流程")
            context.tasker.controller.post_click(1217,510).wait() #消球
            time.sleep(0.2)
            context.tasker.controller.post_click(1053, 631).wait() #闪避
            start_time = time.time()
            while time.time() - start_time < 2:
                time.sleep(0.1)
                context.tasker.controller.post_click(
                    1194,632
                ).wait()  #攻击
            
        else:
            if context.run_recognition("检查u2_囚影", image):  # 检查是否有u2
                while context.run_recognition("检查u2_囚影", image):
                    image = context.tasker.controller.post_screencap().wait().get() # 宿命的囚笼由我斩断
                    print("u2")
                    context.tasker.controller.post_click(910, 631).wait()
            elif context.run_recognition("检查无光值_囚影", image):  # 检查无光值大于474
                print("无光值大于474")
                context.tasker.controller.post_swipe(1055, 629, 1055, 629, 2000).wait() # 生死只在一瞬
                time.sleep(0.3)
                context.tasker.controller.post_swipe(
                    1201, 632, 1201, 632, 2000
                ).wait()  # 登龙
            context.tasker.controller.post_click(1217,510).wait() #消球
            time.sleep(0.3)
            context.tasker.controller.post_click(1053, 631).wait() #闪避
            start_time = time.time()
            while time.time() - start_time < 2:
                time.sleep(0.1)
                context.tasker.controller.post_click(
                    1194,632
                ).wait()  #攻击

        return CustomAction.RunResult(success=True)

        
