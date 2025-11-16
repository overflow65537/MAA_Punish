# Copyright (c) 2024-2025 MAA_Punish
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from custom.action.basics import CombatActions
from maa.context import Context
from maa.custom_action import CustomAction


class LivJimeng(CustomAction): 
    """
    丽芙霁梦 战斗逻辑
    优先级:
    1. 必杀技
    2. 普攻形态1 + 核心
    3. 普攻形态2
    4. 默认普攻
    """
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        
        # 检查普攻形态1的节点
        self.check_attack_1 = {
            "检查普攻1_霁梦": { # 节点名字
                "recognition": {
                    "type": "ImageRecognition", # 类型：图像识别
                    "param": {
                        "template": "自定义战斗/霁梦普攻1.png",
                        "roi": [0, 0, 1920, 1080]
                    }
                }
            }
        }
        
        # 检查普攻形态2的节点
        self.check_attack_2 = {
            "检查普攻2_霁梦": { # 节点名字
                "recognition": {
                    "type": "ImageRecognition", # 类型：图像识别
                    "param": {
                        "template": "自定义战斗/霁梦普攻2.png",
                        "roi": [0, 0, 1920, 1080]
                    }
                }
            }
        }
        
        # 检查核心条的节点
        self.check_core = {
            "检查核心条_霁梦": {
                "recognition": {
                    "type": "ColorMatch",
                    "param": {
                        "roi": [679, 633, 50, 32],
                        "connected": True,
                        "count": 50,
                        "upper": [140, 230, 255],
                        "lower": [120, 220, 240]
                    }
                }
            }
        }
        
        # --- 战斗逻辑 ---
        
        action = CombatActions(context, role_name="丽芙霁梦") 
        action.lens_lock()

        # 优先级 1: 大招检测到有能量就释放
        if action.check_Skill_energy_bar():
            action.logger.info("大招就绪，释放")
            action.use_skill()

        # 优先级 2: 检测到普攻1
        elif action.check_status("检查普攻1_霁梦", self.check_attack_1): 
            action.logger.info("检测到普攻形态1")
            
            # ...则检测核心
            if action.check_status("检查核心条_霁梦", self.check_core): 
                action.logger.info("核心已就绪，长按闪避")
                action.long_press_dodge(1000)
            else:
                action.logger.info("普攻形态1，核心未就绪，执行普攻")
                action.continuous_attack(50, 100)

        # 优先级 3: 检测到普攻2
        elif action.check_status("检查普攻2_霁梦", self.check_attack_2):
            action.logger.info("检测到普攻形态2，直接长按闪避")
            action.long_press_dodge(1000)

        # 优先级 4: 默认普攻
        else:
            action.logger.info("默认状态，执行连续普攻")
            action.continuous_attack(50, 100)
            
        return CustomAction.RunResult(success=True)