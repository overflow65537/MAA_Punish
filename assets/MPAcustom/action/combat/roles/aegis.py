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

class AegisRole(BaseRole):
    def do_perform(self) -> None:
        self.action.lens_lock()
        self.action.attack()

        for _ in range(10):
            self.action.ball_elimination_target(1)
            time.sleep(0.1)
            self.action.attack()
            if self.action.check_Skill_energy_bar():
                for _ in range(10):
                    self.action.use_skill()
                    time.sleep(0.1)
                self.action.auto_qte("a")
                self.action.auxiliary_machine()
                continue

            if ball_count := self.action.count_signal_balls() >= 3:
                for _ in range(3):
                    self.action.ball_elimination_target()
                    time.sleep(0.1)
                self.action.auto_qte("a")
                if self.action.count_signal_balls() == ball_count:
                    self.action.dodge()
                    time.sleep(0.1)
                    self.action.ball_elimination_target()
                self.action.auto_qte("a")
                self.action.auxiliary_machine()
        self.action.attack()
        return
