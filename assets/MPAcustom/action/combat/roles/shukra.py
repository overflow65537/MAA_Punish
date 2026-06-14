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

from __future__ import annotations

import time

from MPAcustom.action.combat.core.role import BaseRole

class ShukraRole(BaseRole):
    """
    启明战斗逻辑
    检查是否存在大招
        释放大招
    检查信号球数量信号球数量大于9
        7秒内循环
            识别信号球
            消球
            如果刚才的球是三消
                再消球触发核心技能
            如果没有球了
                结束
        结束后长按攻击尝试触发冰山
    检查信号球数量信号球数量小于9
        攻击攒球
    """

    def do_perform(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        if self.action.check_Skill_energy_bar():
            self.action.use_skill()  # 万世生死,淬于寒冰
            start_time = time.time()
            while time.time() - start_time < 3:  # 生死喧嚣,归于寂静
                time.sleep(0.1)
                self.action.ball_elimination_target(1)
            self.action.use_skill()
            time.sleep(0.1)
            self.action.auxiliary_machine()
            self.action.switch()
            print("切换完成")
            return
        elif self.action.count_signal_balls() >= 9:  # 信号球数量大于9
            start_time = time.time()
            while time.time() - start_time < 7:
                time.sleep(0.3)
                target = self.action.Arrange_Signal_Balls("any")
                self.action.ball_elimination_target(target)
                self.action.logger.info(f"初次消球")
                if target > 0:
                    time.sleep(0.1)
                    self.action.logger.info(f"三连目标,开始二次消球")
                    self.action.ball_elimination_target(1)  # 单独消球
                elif target == 0:
                    self.action.logger.info(f"信号球空,结束")
                    break
            self.action.logger.info(f"长按攻击")
            self.action.long_press_attack()
        else:
            self.action.logger.info(f"普攻")
            start_time = time.time()
            while time.time() - start_time < 2:
                self.action.attack()  # 攻击
                time.sleep(0.1)
        self.action.attack()
        return
