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
MAA_Punish 特殊战斗识别
作者:overflow65537
"""

from maa.context import Context
from maa.custom_action import CustomAction


class Identify(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        image = context.tasker.controller.post_screencap().wait().get()
        if context.run_recognition("检查露娜·终焉", image):
            context.override_pipeline(
                {
                    "识别人物": {"enabled": False},
                    "战斗中": {"action": "Custom", "custom_action": "Oblivion"},
                }
            )
            print("终焉战斗")
        elif context.run_recognition("检查比安卡·深痕", image):
            context.override_pipeline(
                {
                    "识别人物": {"enabled": False},
                    "战斗中": {"action": "Custom", "custom_action": "Stigmata"},
                }
            )
            print("深痕战斗")
        elif context.run_recognition("检查拉弥亚·深谣", image):
            context.override_pipeline(
                {
                    "识别人物": {"enabled": False},
                    "战斗中": {"action": "Custom", "custom_action": "LostLullaby"},
                }
            )
            print("深谣战斗")
        elif context.run_recognition("检查露西亚·深红囚影", image):
            context.override_pipeline(
                {
                    "识别人物": {"enabled": False},
                    "战斗中": {"action": "Custom", "custom_action": "CrimsonWeave"},
                }
            )
            print("深红囚影")
        elif context.run_recognition("检查露西亚·誓焰", image):
            context.override_pipeline(
                {
                    "识别人物": {"enabled": False},
                    "战斗中": {"action": "Custom", "custom_action": "Pyroath"},
                }
            )
            print("誓焰战斗")
        elif context.run_recognition("检查曲·启明", image):
            context.override_pipeline(
                {
                    "识别人物": {"enabled": False},
                    "战斗中": {"action": "Custom", "custom_action": "Shukra"},
                }
            )
            print("启明战斗")
        else:
            context.override_pipeline(
                {
                    "识别人物": {"enabled": False},
                    "战斗中": {"action": "Custom", "custom_action": "CombatActions"},
                }
            )
            print("未知战斗")

        return CustomAction.RunResult(success=True)
