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

"""通用战斗程序"""

from __future__ import annotations

import time

from MPAcustom.action.combat.core.role import BaseRole


class GeneralFight(BaseRole):
    def do_perform(self) -> None:
        print("开始战斗")
        self.action.lens_lock()
        self.action.attack()
        for _ in range(10):
            if self.combat.context.tasker.stopping:
                return
            self.action.attack()
            self.action.ball_elimination_target()
            self.action.use_skill()
            self.action.auxiliary_machine()
        self.action.attack()
        self.action.auto_qte("a")

        if self.switch_next():
            print("切换完成")
        return
