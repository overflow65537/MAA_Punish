from maa.context import Context
from maa.custom_action import CustomAction
import time

class Oblivion(CustomAction):
    def __execute_action(self, job, action_name: str, timeout=5) -> bool:
        """执行操作并等待结果"""
        print(f"[执行] {action_name}")
        try:
            # 等待操作完成（带超时机制）
            start_time = time.time()
            while not job.done:
                if time.time() - start_time > timeout:
                    print(f"[超时] {action_name} 执行超时")
                    return False
                time.sleep(0.1)
            
            # 检查最终状态
            if job.succeeded:
                print(f"[成功] {action_name}")
                return True
            print(f"[失败] {action_name} 状态码: {job.status}")
            return False
            
        except Exception as e:
            print(f"[异常] {action_name} 错误: {str(e)}")
            return False

    def __check_moon(self, context: Context) -> bool:
        """检查残月值"""
        try:
            # 获取截图
            screencap_job = context.tasker.controller.post_screencap()
            if not self.__execute_action(screencap_job, "状态检查"):
                return False
            
            # 识别残月值
            image = screencap_job.wait().get()  # 获取截图结果
            return context.run_recognition("检查残月值_终焉", image)
        except Exception as e:
            print(f"[异常] 残月值检查失败: {str(e)}")
            return False

    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        try:
            # 初始残月值检查
            if self.__check_moon(context):
                print("[状态] 残月值满")
                # 长按普攻
                swipe_job = context.tasker.controller.post_swipe(1193, 633, 1198, 638, 1200)
                if not self.__execute_action(swipe_job, "长按攻击"):
                    return CustomAction.RunResult(success=False)
                
                # 释放大招
                ult_job = context.tasker.controller.post_click(915, 626)
                return CustomAction.RunResult(
                    success=self.__execute_action(ult_job, "释放大招")
                )

            # 消球操作
            print("[阶段] 执行消球")
            for i in range(3):  # 最多尝试3次消球
                ball_job = context.tasker.controller.post_click(1215, 510)
                if not self.__execute_action(ball_job, f"消球 #{i+1}"):
                    continue
                
                # 消球后检查残月值
                if self.__check_moon(context):
                    print("[状态] 消球后残月值满")
                    # 长按普攻
                    swipe_job = context.tasker.controller.post_swipe(1193, 633, 1198, 638, 1200)
                    if not self.__execute_action(swipe_job, "长按攻击"):
                        continue
                    
                    # 释放大招
                    ult_job = context.tasker.controller.post_click(915, 626)
                    return CustomAction.RunResult(
                        success=self.__execute_action(ult_job, "释放大招")
                    )

            # 普攻阶段
            print("[阶段] 进入普攻循环")
            attack_start = time.time()
            while time.time() - attack_start < 3.0:  # 攻击持续3秒
                # 执行普攻
                attack_job = context.tasker.controller.post_click(1197, 636)
                if not self.__execute_action(attack_job, "普攻"):
                    time.sleep(0.2)
                    continue
                
                # 动态调整攻击间隔
                elapsed = time.time() - attack_start
                interval = 0.4 if elapsed < 1.5 else 0.25
                time.sleep(interval)
                
                # 中途检查残月值
                if elapsed > 1.0 and self.__check_moon(context):
                    print("[状态] 攻击过程中残月值满")
                    # 长按普攻
                    swipe_job = context.tasker.controller.post_swipe(1193, 633, 1198, 638, 1200)
                    if not self.__execute_action(swipe_job, "紧急长按攻击"):
                        break
                    
                    # 释放大招
                    ult_job = context.tasker.controller.post_click(915, 626)
                    return CustomAction.RunResult(
                        success=self.__execute_action(ult_job, "紧急释放大招")
                    )

            return CustomAction.RunResult(success=True)
            
        except Exception as e:
            print(f"[严重错误] 执行流程中断: {str(e)}")
            return CustomAction.RunResult(success=False)