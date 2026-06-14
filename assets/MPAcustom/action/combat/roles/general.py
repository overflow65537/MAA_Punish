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

"""
MAA_Punish
MAA_Punish 通用战斗角色策略
作者:overflow65537
"""

from __future__ import annotations

from MPAcustom.action.combat.role import BaseRole

_COMBO_ROUNDS = 10


class GeneralRole(BaseRole):
    """通用战斗逻辑（由 GeneralFight 迁移，每 tick 推进一步）。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._combo_round = 0
        self._combo_sub = 0

    def reset_state(self) -> None:
        super().reset_state()
        self._combo_round = 0
        self._combo_sub = 0

    def do_perform(self) -> None:
        if self.phase == "idle":
            self.action.lens_lock()
            self.action.attack()
            self.phase = "combo"
            return

        if self.phase == "combo":
            self._do_combo_step()
            return

        if self.phase == "finish":
            self.action.attack()
            self.action.auto_qte("a")
            self.switch_next()
            self.phase = "done"
            return

        if self.phase == "done":
            self.action.attack()

    def _do_combo_step(self) -> None:
        if self._combo_sub == 0:
            self.action.attack()
        elif self._combo_sub == 1:
            self.action.ball_elimination_target()
        elif self._combo_sub == 2:
            self.action.use_skill()
        else:
            self.action.auxiliary_machine()

        self._combo_sub += 1
        if self._combo_sub >= 4:
            self._combo_sub = 0
            self._combo_round += 1

        if self._combo_round >= _COMBO_ROUNDS:
            self.phase = "finish"
            self._combo_round = 0
            self._combo_sub = 0
