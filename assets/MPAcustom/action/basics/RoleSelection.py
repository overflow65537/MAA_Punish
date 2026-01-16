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
MAA_Punish 选择角色
作者:overflow65537
"""

from maa.context import Context
from maa.custom_action import CustomAction
from maa.define import TemplateMatchResult, OCRResult, ColorMatchResult
import json
import os
import numpy


from MPAcustom.action.tool.LoadSetting import ROLE_ACTIONS
from MPAcustom.logger_component import LoggerComponent


class RoleSelection(CustomAction):
    def __init__(self):
        super().__init__()
        self._logger_component = LoggerComponent(__name__)
        self.logger = self._logger_component.logger

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        condition = json.loads(argv.custom_action_param)
        if condition is None:
            condition = {}
        role_dict = ROLE_ACTIONS.copy()
        role_node = context.get_node_data("角色权重")
        _cache = False
        if role_node:
            self.logger.info(f"读取缓存: {role_node}")
            role = role_node.get("focus", {})
            _cache = True
        else:
            self.logger.info(f"未读取到缓存, 开始识别")
            role = {}

            for _ in range(int(condition.get("max_try", 5))):
                if context.tasker.stopping:
                    return CustomAction.RunResult(success=True)
                role.update(
                    self.recognize_role(
                        context,
                        role_dict,
                        condition.get("cage", False),
                        condition.get("roguelike_3_mode", 0),
                    )
                )
                if (
                    not condition.get("cage")
                    and condition.get("pick", "") in role.keys()
                ):
                    break
                context.run_action("滑动_选人")

        print(f"角色列表: {role}")

        role_weight = self.calculate_weight(role, condition)
        self.logger.info(f"条件: {condition}")
        self.logger.info(f"角色权重: {role_weight}")
        if (
            not (not condition.get("cage") and condition.get("pick", "") in role.keys())
            and not _cache
        ):
            for _ in range(int(condition.get("max_try", 4))):
                if context.tasker.stopping:
                    return CustomAction.RunResult(success=True)
                context.run_action("反向滑动_选人")
        return CustomAction.RunResult(success=True)

    def recognize_role(
        self,
        context: Context,
        role_actions: dict,
        cage: bool = False,
        roguelike_3_mode: int = 0,
    ) -> dict:

        # 对每个角色进行识别
        role = {}
        image = context.tasker.controller.post_screencap().wait().get()
        for role_name, role_action in role_actions.items():

            pipeline_override = {
                "识别角色": {
                    "recognition": {
                        "param": {"template": role_action["template"]},
                    },
                }
            }

            result = context.run_recognition(
                entry="识别角色",
                image=image,
                pipeline_override=pipeline_override,
            )

            if (
                result
                and result.hit
                and isinstance(result.best_result, TemplateMatchResult)
            ):
                for role_reco in result.filtered_results:
                    # 检查识别结果并提取box信息
                    if not isinstance(role_reco, TemplateMatchResult):
                        self.send_msg(context, f"未检测到对应人物: {role_name}")
                        return {}
                    print(role_reco.box)

                    trial_reco = context.run_recognition(
                        entry="识别试用角色",
                        image=image,
                        pipeline_override={
                            "识别试用角色": {
                                "recognition": {
                                    "param": {"roi": role_reco.box},
                                },
                            }
                        },
                    )
                    trial = False
                    if trial_reco and trial_reco.hit:
                        trial = True
                    print(f"role_name: {role_name} trial: {trial}")

                    trial_label = " 试用" if trial and "[试用]" not in role_name else ""
                    self.logger.info(f"识别到角色: {role_name}{trial_label}")

                    display_name = (
                        role_name + "[试用]"
                        if trial and "[试用]" not in role_name
                        else role_name
                    )
                    metadata = role_action.get("metadata", {})
                    role[display_name] = (
                        metadata.copy() if isinstance(metadata, dict) else {}
                    )

                    context.run_recognition(
                        entry="识别战斗参数",
                        image=image,
                        pipeline_override={
                            "识别战斗参数": {
                                "recognition": {
                                    "param": {"roi": role_reco.box},
                                },
                            }
                        },
                    )
                    power_reco = context.run_recognition(
                        entry="识别战力",
                        image=image,
                    )

                    if (
                        power_reco
                        and power_reco.hit
                        and isinstance(power_reco.best_result, OCRResult)
                    ):
                        if power_reco.best_result.text.isdigit():
                            role[display_name]["power"] = int(
                                power_reco.best_result.text
                            )
                        else:
                            role[display_name]["power"] = 0
                        print(
                            f"识别到角色: {display_name} 战力: {role[display_name]['power']}"
                        )

                    if cage:
                        if (
                            cage_3_result := context.run_recognition(
                                entry="识别囚笼次数3",
                                image=image,
                                pipeline_override={
                                    "识别囚笼次数3": {
                                        "recognition": {
                                            "param": {
                                                "roi": role_reco.box,
                                            },
                                        }
                                    }
                                },
                            )
                        ) is not None and cage_3_result.hit:
                            role[display_name]["cage"] = 3
                        elif (
                            cage_2_result := context.run_recognition(
                                entry="识别囚笼次数2",
                                image=image,
                                pipeline_override={
                                    "识别囚笼次数2": {
                                        "recognition": {
                                            "param": {
                                                "roi": role_reco.box,
                                            },
                                        }
                                    }
                                },
                            )
                        ) is not None and cage_2_result.hit:
                            role[display_name]["cage"] = 2
                        elif (
                            cage_1_result := context.run_recognition(
                                entry="识别囚笼次数1",
                                image=image,
                                pipeline_override={
                                    "识别囚笼次数1": {
                                        "recognition": {
                                            "param": {
                                                "roi": role_reco.box,
                                            },
                                        }
                                    }
                                },
                            )
                        ) is not None and cage_1_result.hit:
                            role[display_name]["cage"] = 1
                        else:
                            role[display_name]["cage"] = 0

                    if roguelike_3_mode == 1:
                        mastery_result = context.run_recognition(
                            entry="识别精通等级",
                            image=image,
                            pipeline_override={
                                "识别精通等级": {
                                    "recognition": {
                                        "param": {"roi": role_reco.box},
                                    }
                                }
                            },
                        )
                        role[display_name]["master_level"] = bool(
                            mastery_result and mastery_result.hit
                        )
        return role

    # 计算权重
    def calculate_weight(self, role_info: dict, condition: dict[str, dict]) -> dict:
        """
        公式
        权重 = ( 战力 * 0.5 + ( 属性分数 * 45) + (代数分数 * 2300) + (是否被选中 * 10000) + (是否精通等级没满 * 10000)) * 是否有次数
        """
        weight = {}

        for role_name, info in role_info.items():
            # 战力
            power = info.get("power", 0)
            # 属性分数
            attribute_score = info.get(condition.get("need_element", ""), 0)
            # 代数分数
            element_score = info.get("generation", 0)
            # 是否有次数
            has_count = info.get("cage", 0)
            # 肉鸽3模式 0代表初始招募能量4，只需要提取是否被肉鸽选中。1代表初始招募能量3，只提取精通等级
            # 是否被选中
            if condition.get("roguelike_3_mode", 0) == 1:
                is_pick = False
                is_master_level_not_full = info.get("master_level", False)
            else:
                is_pick = role_name == condition.get("pick", "")
                is_master_level_not_full = False

            # 精通等级是否未满

            # 权重计算
            # 1. 战力
            power_weight = power * 0.5

            # 1. 属性分数
            attribute_weight = attribute_score * 45

            # 2. 代数分数
            generation_weight = element_score * 2300

            # 3. 精通等级分数
            master_level_weight = 10000 if is_master_level_not_full else 0

            # 4. 被选中加成
            pick_bonus = 10000 if is_pick else 0

            # 5. 基础权重 = ( 属性 + 代数 + 精通) * 是否有次数
            base_weight = (
                power_weight
                + attribute_weight
                + generation_weight
                + master_level_weight
                + pick_bonus
            ) * (1 if (not condition.get("cage", False)) or has_count else 0)

            # 6. 最终权重 = 基础权重 + 选中加成
            w = base_weight

            self.logger.debug(
                f"{role_name}: 战力={power_weight}, 属性分={attribute_weight}, 代数分={generation_weight}, "
                f"精通分={master_level_weight}, 选中加成={pick_bonus}, 基础权重={base_weight}, 是否有次数={bool(1 if (not condition.get("cage", False)) or has_count else 0)}, 最终权重={w}"
            )
            print(f"{role_name}: 权重={w}")
            weight[role_name] = w

        return weight

    def save_screenshot(self, image: numpy.ndarray, img_type: str) -> bool:

        import struct
        import zlib
        import time

        height, width, _ = image.shape
        current_time = img_type + "_" + time.strftime("%Y-%m-%d_%H-%M-%S") + ".png"
        debug_path = os.path.join("debug", current_time)
        if not os.path.exists("debug"):
            os.makedirs("debug")

        def png_chunk(chunk_type, data):
            chunk = chunk_type + data
            return (
                struct.pack("!I", len(data))
                + chunk
                + struct.pack("!I", zlib.crc32(chunk))
            )

        # Convert BGR to RGB
        image = image[:, :, [2, 1, 0]]

        raw_data = b"".join(b"\x00" + image[i, :, :].tobytes() for i in range(height))
        ihdr = struct.pack("!2I5B", width, height, 8, 2, 0, 0, 0)
        idat = zlib.compress(raw_data, level=9)

        with open(debug_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")
            f.write(png_chunk(b"IHDR", ihdr))
            f.write(png_chunk(b"IDAT", idat))
            f.write(png_chunk(b"IEND", b""))
        return True

    def send_msg(self, context: Context, msg: str):
        msg_node = {
            "发送消息_这是程序自动生成的node所以故意写的很长来防止某一天想不开用了这个名字导致报错": {
                "focus": {"Node.Recognition.Succeeded": msg}
            }
        }
        context.run_task(
            "发送消息_这是程序自动生成的node所以故意写的很长来防止某一天想不开用了这个名字导致报错",
            pipeline_override=msg_node,
        )
