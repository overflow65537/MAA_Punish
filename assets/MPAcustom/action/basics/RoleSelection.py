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

import time
from maa.context import Context
from maa.custom_action import CustomAction
from maa.define import TemplateMatchResult, OCRResult, ColorMatchResult
import datetime
import json
import os
from pathlib import Path
import numpy


from MPAcustom.action.tool.LoadSetting import ROLE_ACTIONS
from MPAcustom.logger_component import LoggerComponent


class RoleSelection(CustomAction):
    def __init__(self):
        super().__init__()
        self._logger_component = LoggerComponent(__name__)
        self.logger = self._logger_component.logger

    def _cache_path(self) -> Path:
        return (
            Path(__file__).resolve().parents[2]
            / "recognition"
            / "exclusives"
            / "role_cache.json"
        )

    def _current_week(self) -> int:
        return datetime.date.today().isocalendar().week

    def _load_cache(self) -> dict | None:
        cache_path = self._cache_path()
        if not cache_path.exists():
            return None
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(cache_data, dict):
            return None
        last_time = cache_data.get("last_time")
        if last_time is None:
            return None
        try:
            last_week = int(last_time)
        except (TypeError, ValueError):
            return None
        if last_week != self._current_week():
            return None
        focus = cache_data.get("focus")
        if not isinstance(focus, dict) or not focus:
            return None
        return focus

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        condition = json.loads(argv.custom_action_param)
        need_cache = False
        if condition is None:
            condition = {}
        elif condition.get("cache"):
            need_cache = True
        roguelike_3_mode = context.get_node_data("肉鸽模式_配置")
        if roguelike_3_mode:
            roguelike_3_mode = roguelike_3_mode.get("focus")
        else:
            roguelike_3_mode = None
        print(f"肉鸽模式: {roguelike_3_mode}")
        pick = context.get_node_data("选择人物_配置")
        if pick and pick.get("focus", None):
            pick = pick.get("focus", "")
        else:
            pick = ""

        condition.update(
            {
                "roguelike_3_mode": roguelike_3_mode,
                "pick": pick,
            }
        )
        role_dict = ROLE_ACTIONS.copy()

        role = None
        if roguelike_3_mode is None and not need_cache:
            role = self._load_cache()
            if role:
                self.logger.info("读取文件缓存成功")

        if not role:
            self.logger.info("未读取到缓存, 开始识别")
            role = {}

            for _ in range(
                int(condition.get("max_try", 5 if roguelike_3_mode is None else 15))
            ):
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
                context.run_action("滑动_选人")
            if need_cache:
                self.save_cache(role)
                return CustomAction.RunResult(success=True)
            for _ in range(
                int(condition.get("max_try", 5 if roguelike_3_mode is None else 15))
            ):
                if context.tasker.stopping:
                    return CustomAction.RunResult(success=True)
                context.run_action("反向滑动_选人")

        role_weight = self.calculate_weight(role, condition)
        best_team = self.select_best_team(role_weight)
        self.logger.info(f"条件: {condition}")
        self.logger.info(f"角色权重: {role_weight}")
        attacker_name = best_team.get("attacker", {}).get("name")
        tank_name = best_team.get("tank", {}).get("name")
        support_name = best_team.get("support", {}).get("name")
        self.logger.info(
            f"队伍构成: {support_name or '无'} {attacker_name or '无'} {tank_name or '无'}"
        )
        self.send_msg(
            context,
            f"队伍构成: {support_name or '无'} {attacker_name or '无'} {tank_name or '无'}",
        )
        if attacker_name and self.find_role(
            context, role_dict, attacker_name, 5 if roguelike_3_mode is None else 16
        ):
            context.run_task("编入队伍")

        if condition.get("roguelike_3_mode") is None:
            print("非肉鸽模式")
            if tank_name:
                context.run_task("打开黄色位置")
                if self.find_role(context, role_dict, tank_name):
                    context.run_task("编入队伍")
                else:
                    time.sleep(0.5)
                    context.run_task("返回")

            if support_name:
                context.run_task("打开蓝色位置")
                if self.find_role(context, role_dict, support_name):
                    context.run_task("编入队伍")
                else:
                    time.sleep(0.5)
                    context.run_task("返回")
        # 缓存数据
        if roguelike_3_mode is None:
            if condition.get("cage"):
                for selected_name in (attacker_name, tank_name, support_name):
                    if not selected_name:
                        continue
                    role_key = selected_name
                    if role_key not in role:
                        role_key = selected_name.replace("[试用]", "")
                    if role_key in role:
                        role[role_key]["cage"] = 0
            context.override_pipeline({"角色权重": {"focus": role}})
            self.logger.info(f"缓存数据: {role}")
            self.save_cache(role)

        return CustomAction.RunResult(success=True)

    def find_role(
        self, context: Context, role_dict: dict, role_name: str, max_try: int = 16
    ) -> bool:
        _image_cache=[]
        if "[试用]" in role_name:
            role_name = role_name.replace("[试用]", "")
            trial = True
        else:
            trial = False
        for _ in range(max_try):
            image = context.tasker.controller.post_screencap().wait().get()
            _image_cache.append(image)
            pipeline_override = {
                "识别角色": {
                    "recognition": {
                        "param": {"template": role_dict[role_name]["template"]},
                    },
                }
            }
            role_reco = context.run_recognition(
                entry="识别角色",
                image=image,
                pipeline_override=pipeline_override,
            )
            if role_reco and role_reco.hit:
                if trial:
                    for role in role_reco.filtered_results:
                        trial_pipeline_override = {
                            "识别试用角色": {
                                "recognition": {
                                    "param": {"roi": role.box},  # type: ignore
                                },
                            }
                        }
                        trial_reco = context.run_recognition(
                            "识别试用角色",
                            image=image,
                            pipeline_override=trial_pipeline_override,
                        )
                        if trial_reco and trial_reco.hit:

                            for _ in range(4):
                                context.tasker.controller.post_click(
                                    role.box[0] + role.box[2], role.box[1] + role.box[3]  # type: ignore
                                ).wait()
                                image = (
                                    context.tasker.controller.post_screencap()
                                    .wait()
                                    .get()
                                )
                                reco = context.run_recognition("编入队伍", image)
                                if reco and reco.hit:
                                    break
                                time.sleep(0.5)
                            return True
                else:
                    for _ in range(4):
                        context.tasker.controller.post_click(
                            role_reco.best_result.box[0] + role_reco.best_result.box[2] // 2, role_reco.best_result.box[1] + role_reco.best_result.box[3] // 2  # type: ignore
                        ).wait()
                        image = context.tasker.controller.post_screencap().wait().get()
                        reco = context.run_recognition("编入队伍", image)
                        if reco and reco.hit:
                            break
                        time.sleep(0.5)
                    return True
            context.run_action("滑动_选人")
        print(f"未识别到角色")
        self.logger.info(f"未识别到角色{role_name}")
        self.send_msg(context, f"未识别到角色{role_name}")
        for idx,error_image in enumerate(_image_cache):
            self.save_screenshot(error_image ,f"{role_name}_{idx+1}")
        return False

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
        权重 = ( 战力 * 0.3 + ( 属性分数 * 60) + (代数分数 * 2300) + (是否被选中 * 20000) + (是否精通等级没满 * 10000)) * 是否有次数
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
                is_pick = role_name == condition.get("pick", "")
                is_master_level_not_full = info.get("master_level", False)
            else:
                is_pick = role_name == condition.get("pick", "")
                is_master_level_not_full = False

            # 精通等级是否未满

            # 权重计算
            # 1. 战力
            power_weight = power * 0.3

            # 1. 属性分数
            attribute_weight = attribute_score * 60

            # 2. 代数分数
            generation_weight = element_score * 2300

            # 3. 精通等级分数
            master_level_weight = 10000 if is_master_level_not_full else 0

            # 4. 被选中加成
            pick_bonus = 20000 if is_pick else 0

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
            weight[role_name] = w

        return weight

    def select_best_team(self, role_weight: dict) -> dict:
        best = {
            "attacker": {"name": None, "weight": 0},
            "tank": {"name": None, "weight": 0},
            "support": {"name": None, "weight": 0},
        }
        candidates = []
        for role_name, w in role_weight.items():
            if w <= 0:
                continue
            is_trial = "[试用]" in role_name
            base_name = role_name.replace("[试用]", "")
            role_type_value = ROLE_ACTIONS.get(base_name, {}).get("type", "")
            role_type_key = str(role_type_value).lower()
            if role_type_key not in best:
                continue
            candidates.append((role_name, w, role_type_key, base_name, is_trial))

        unique_candidates = {}
        for role_name, w, role_type_key, base_name, is_trial in candidates:
            if base_name not in unique_candidates:
                unique_candidates[base_name] = (
                    role_name,
                    w,
                    role_type_key,
                    base_name,
                    is_trial,
                )
                continue
            existing = unique_candidates[base_name]
            if w > existing[1] or (w == existing[1] and is_trial and not existing[4]):
                unique_candidates[base_name] = (
                    role_name,
                    w,
                    role_type_key,
                    base_name,
                    is_trial,
                )
        candidates = list(unique_candidates.values())

        if len(candidates) < 3:
            candidates.sort(key=lambda item: item[1], reverse=True)
            if candidates:
                best["attacker"] = {
                    "name": candidates[0][0],
                    "weight": candidates[0][1],
                }
                remaining = candidates[1:]
            else:
                remaining = []
            for role_name, w, role_type_key, _base_name, _is_trial in remaining:
                if w > best[role_type_key]["weight"]:
                    best[role_type_key] = {"name": role_name, "weight": w}
            return best

        support_candidates = []
        tank_candidates = []
        for role_name, w, role_type_key, _base_name, _is_trial in candidates:
            if role_type_key == "support":
                support_candidates.append((role_name, w))
            if role_type_key == "tank":
                tank_candidates.append((role_name, w))
            if w > best[role_type_key]["weight"]:
                best[role_type_key] = {"name": role_name, "weight": w}

        if not best["tank"]["name"] and len(support_candidates) >= 2:
            support_candidates.sort(key=lambda item: item[1], reverse=True)
            second_support = support_candidates[1]
            best["tank"] = {"name": second_support[0], "weight": second_support[1]}

        if not best["attacker"]["name"]:
            combined_candidates = tank_candidates + support_candidates
            exclude_names = {
                name for name in (best["tank"]["name"], best["support"]["name"]) if name
            }
            combined_candidates = [
                item for item in combined_candidates if item[0] not in exclude_names
            ]
            if combined_candidates:
                combined_candidates.sort(key=lambda item: item[1], reverse=True)
                best["attacker"] = {
                    "name": combined_candidates[0][0],
                    "weight": combined_candidates[0][1],
                }

        return best

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

    def save_cache(self, role: dict):
        cache_path = self._cache_path()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_data = {
            "last_time": self._current_week(),
            "focus": role,
        }
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
