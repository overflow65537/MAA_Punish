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

"""InverseCrown combat strategy."""

from __future__ import annotations

import time

from MPAcustom.action.combat.core.role import BaseRole


class InverseCrown(BaseRole):
    def do_perform(self) -> None:
        self.action.lens_lock()
        self.action.attack()
        if self.action.check_status("检查逆冕能量即将满"):
            self.action.logger.info("大招")
            self.skill_use()

        elif self.action.count_signal_balls() >= 16:
            self.action.logger.info("球数满足条件，进行球消")
            self.action.ball_elimination_target()

        elif self.action.count_signal_balls() > 7 and self.action.check_status(
            "检查逆冕特殊球"
        ):
            self.action.logger.info("特殊球就绪")
            self.combat.context.run_action(
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

            self.skill_use()

        else:
            self.action.logger.info("特殊球未就绪")
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

    def skill_use(self) -> None:
        cage = self.combat.context.get_node_data("选择角色程序")
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
