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


_SELECTION_MODE_TABLE: dict[str, dict] = {
    "standard": {
        "roguelike_equivalent": None,
        "scan_then_return": False,
        "default_max_try": 15,
    },
    "cache_refresh": {
        "roguelike_equivalent": None,
        "scan_then_return": True,
        "default_max_try": 15,
    },
    "roguelike_1": {
        "roguelike_equivalent": 1,
        "scan_then_return": False,
        "default_max_try": 1,
    },
    "roguelike_2": {
        "roguelike_equivalent": 2,
        "scan_then_return": False,
        "default_max_try": 1,
    },
    "roguelike_3": {
        "roguelike_equivalent": 3,
        "scan_then_return": False,
        "default_max_try": 5,
    },
    "roguelike_4": {
        "roguelike_equivalent": 4,
        "scan_then_return": False,
        "default_max_try": 1,
    },
}


class RoleSelection(CustomAction):
    def __init__(self):
        super().__init__()
        self._logger_component = LoggerComponent(__name__)
        self.logger = self._logger_component.logger

    def _cache_path(self) -> Path:
        return Path(__file__).resolve().parents[3] / "role_cache.json"

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

    def _get_role_element_task(self, role_dict: dict, role_name: str) -> str | None:
        base_role_name = role_name.replace("[试用]", "")
        role_action = role_dict.get(base_role_name, {})
        metadata = role_action.get("metadata", {})
        if not isinstance(metadata, dict):
            return None

        element_task_map = {
            "physical": "打开物理属性",
            "fire": "打开火属性",
            "ice": "打开冰属性",
            "lightning": "打开雷属性",
            "dark": "打开暗属性",
            "nihil": "打开空属性",
        }

        matched_task = None
        matched_score = float("-inf")
        for element_key, task_name in element_task_map.items():
            score = metadata.get(element_key)
            if isinstance(score, (int, float)) and score > matched_score:
                matched_task = task_name
                matched_score = score

        return matched_task

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        param = json.loads(argv.custom_action_param) if argv.custom_action_param else {}
        if param is None:
            param = {}

        node_data = context.get_node_data(argv.node_name) or {}
        attach: dict = node_data.get("attach", {}) or {}

        selection_mode: str = (
            attach["selection_mode"]
            if "selection_mode" in attach
            else param.get("selection_mode", "standard")
        )
        need_multi: bool = (
            bool(attach["need_multi"])
            if "need_multi" in attach
            else bool(param.get("need_multi", False))
        )

        mode_cfg = _SELECTION_MODE_TABLE.get(selection_mode, _SELECTION_MODE_TABLE["standard"])
        roguelike_equivalent: int | None = mode_cfg["roguelike_equivalent"]
        scan_then_return: bool = mode_cfg["scan_then_return"]

        pick: list = attach.get("pick", [])
        cage: bool = bool(attach.get("cage", False))
        need_element: str = attach.get("need_element", "") or ""
        max_try: int = int(attach.get("max_try", mode_cfg["default_max_try"]))

        self.logger.info(
            f"开始执行配队: selection_mode={selection_mode}, roguelike_equivalent={roguelike_equivalent}, "
            f"scan_then_return={scan_then_return}, need_multi={need_multi}, "
            f"cage={cage}, need_element={need_element!r}, pick={pick}, max_try={max_try}"
        )

        condition = {
            "roguelike_mode": roguelike_equivalent,
            "pick": pick,
            "cage": cage,
            "need_element": need_element,
        }
        role_dict = ROLE_ACTIONS.copy()

        role = None
        if roguelike_equivalent is None and not scan_then_return:
            role = self._load_cache()
            if role:
                self.logger.info("读取文件缓存成功")

        if not role:
            self.logger.info("未读取到缓存, 开始识别")
            role = {}
            scan_count = max_try
            performed_slide_count = 0

            self.logger.info(
                f"角色识别计划滑动次数: scan_count={scan_count}, roguelike_equivalent={roguelike_equivalent}"
            )

            for _ in range(scan_count):
                if context.tasker.stopping:
                    return CustomAction.RunResult(success=True)
                role.update(
                    self.recognize_role(
                        context,
                        role_dict,
                        cage,
                        roguelike_equivalent or 0,
                    )
                )
                image = context.tasker.controller.post_screencap().wait().get()
                check_role = context.run_recognition("检查到未解锁角色", image)
                if check_role is not None and check_role.hit:
                    self.logger.info("检测到未解锁角色, 可能已经滑到底了")
                    break
                context.run_action("滑动_选人")
                performed_slide_count += 1

            if scan_then_return:
                for r in role.values():
                    r["cage"] = 3  # 强制设置为有次数
                self.save_cache(role)
                self.logger.info(f"识别完成并写入缓存, 共识别到角色数量: {len(role)}")
                return CustomAction.RunResult(success=True)

            reset_count = performed_slide_count + 1
            self.logger.info(
                f"角色识别实际滑动次数: performed_slide_count={performed_slide_count}, "
                f"reset_count={reset_count}"
            )
            for _ in range(reset_count):
                if context.tasker.stopping:
                    return CustomAction.RunResult(success=True)
                context.run_action("反向滑动_选人")

        role_weight = self.calculate_weight(role, condition)
        self.logger.info(f"根据识别结果计算权重完成, 共 {len(role_weight)} 个角色")
        best_team = self.select_best_team(role_weight)
        self.logger.info(f"条件: {condition}")
        self.logger.info(f"角色权重: {role_weight}")
        attacker_name = best_team.get("attacker", {}).get("name")
        tank_name = best_team.get("tank", {}).get("name")
        support_name = best_team.get("support", {}).get("name")

        # 仅在 need_multi 为 True 且 roguelike_mode 为空(None) 时显示名称，否则显示“无”
        display_tank_name = tank_name if need_multi and roguelike_equivalent is None else None
        display_support_name = support_name if need_multi and roguelike_equivalent is None else None

        self.logger.info(
            f"队伍构成: {display_support_name or '无'} {attacker_name or '无'} {display_tank_name or '无'}"
        )
        self.send_msg(
            context,
            f"队伍构成: {display_support_name or '无'} {attacker_name or '无'} {display_tank_name or '无'}",
        )
        if roguelike_equivalent is None and cage:
            for selected_name in (attacker_name, tank_name, support_name):
                if not selected_name:
                    continue
                if not need_multi and selected_name != attacker_name:
                    continue
                role_key = selected_name
                self.logger.info(f"{role_key} 选中, 清除次数")
                if role_key not in role:
                    role_key = selected_name.replace("[试用]", "")
                if role_key in role:
                    role[role_key]["cage"] = 0
            self.logger.info(f"缓存数据: {role}")
            self.save_cache(role)

        if attacker_name and self.find_role(
            context, role_dict, attacker_name, 16 if roguelike_equivalent is None else 5
        ):
            context.run_task("编入队伍")
        else:
            time.sleep(0.5)
            self.send_msg(context, f"未找到{attacker_name}")
            context.run_task("返回主菜单")
            context.run_action("停止任务")

        if need_multi and roguelike_equivalent is None:
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

        return CustomAction.RunResult(success=True)

    def find_role(
        self,
        context: Context,
        role_dict: dict,
        role_name: str,
        max_try: int = 16,
        role_element: str | None = None,
    ) -> bool:
        _image_cache = []
        if role_element is None:
            role_element = self._get_role_element_task(role_dict, role_name)
        if "[试用]" in role_name:
            role_name = role_name.replace("[试用]", "")
            trial = True
        else:
            trial = False
        self.logger.info(
            f"开始查找角色: {role_name}, max_try={max_try}, trial角色={trial}"
        )
        if role_element:
            self.logger.info(f"角色元素要求: {role_element}")
            context.run_task(role_element)

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
            if not trial:  # 非试用角色不识别试用标识
                pipeline_override["识别试用角色"] = {
                    "recognition": {
                        "param": {
                            "lower": [0, 0, 0],
                            "upper": [255, 255, 255],
                        },
                    }
                }
            role_reco = context.run_recognition(
                entry="找到角色",
                image=image,
                pipeline_override=pipeline_override,
            )
            if role_reco and role_reco.hit:
                self.logger.info(f"找到角色 {role_name}, 开始尝试编入队伍")
                for _ in range(4):
                    if trial:
                        x = role_reco.box[0] + 34  # type: ignore[index]
                        y = role_reco.box[1] + role_reco.box[3] + 34  # type: ignore[index]
                        context.tasker.controller.post_click(
                            x, y
                        ).wait()
                    else:
                        context.tasker.controller.post_click(
                            role_reco.box[0] + role_reco.box[2] // 2, role_reco.box[1] + role_reco.box[3] // 2  # type: ignore
                        ).wait()
                    image = context.tasker.controller.post_screencap().wait().get()
                    reco = context.run_recognition("编入队伍", image)
                    time.sleep(0.2)
                    if reco and reco.hit:
                        self.logger.info(f"角色 {role_name} 编入队伍识别成功")
                        break
                return True
            context.run_action("滑动_选人")
        print(f"未识别到角色")
        self.logger.info(f"未识别到角色{role_name}")
        self.send_msg(context, f"未识别到角色{role_name}")
        for idx, error_image in enumerate(_image_cache):
            self.save_screenshot(error_image, f"{role_name}_{idx+1}")
        return False

    def recognize_role(
        self,
        context: Context,
        role_actions: dict,
        cage: bool = False,
        roguelike_mode: int = 0,
    ) -> dict:

        # 对每个角色进行识别
        self.logger.info(
            f"开始整页角色识别, cage={cage}, roguelike_mode={roguelike_mode}"
        )
        role = {}
        image = context.tasker.controller.post_screencap().wait().get()
        checked_count = 0
        for role_name, role_action in role_actions.items():
            checked_count += 1
            if checked_count % 10 == 0:
                self.logger.info(f"角色识别进度:  已识别到 {len(role)} 个角色")
            if context.tasker.stopping:
                return role

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
                is_have_role = context.run_recognition(
                    entry="检查人物是否拥有",
                    image=image,
                )
                if is_have_role and is_have_role.hit:
                    self.logger.info(f"角色 {role_name} 未拥有")
                    return role
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

                    if roguelike_mode == 1:
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
        self.logger.info(f"整页角色识别结束, 共识别到角色数量: {len(role)}")
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
            # 肉鸽模式 0代表初始招募能量4，只需要提取是否被肉鸽选中。1代表初始招募能量3，只提取精通等级
            # 是否被选中
            if condition.get("roguelike_mode", 0) == 1:
                is_pick = role_name.replace("[试用]", "") in condition.get("pick", [])
                is_master_level_not_full = info.get("master_level", False)
            else:
                is_pick = role_name.replace("[试用]", "") in condition.get("pick", [])
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
                f"精通分={master_level_weight}, 选中加成={pick_bonus}, 基础权重={base_weight}, "
                f"是否有次数={bool(1 if (not condition.get('cage', False)) or has_count else 0)}, 最终权重={w}"
            )
            weight[role_name] = w

        return weight

    def select_best_team(self, role_weight: dict) -> dict:
        self.logger.info(f"开始从 {len(role_weight)} 个角色中筛选最佳队伍")

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

            self.logger.info(f"候选人不足三人, 使用降级策略得到队伍: {best}")
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

        self.logger.info(f"筛选完成, 最终队伍: {best}")
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
        self.logger.info(f"正在保存缓存到 {cache_path}, 数据: {role}")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        # 保留 CacheRole 使用的字段（main_update_at / cage_update_week 等），避免被覆盖丢失。
        existing: dict = {}
        try:
            if cache_path.exists():
                with open(cache_path, "r", encoding="utf-8") as rf:
                    loaded = json.load(rf)
                if isinstance(loaded, dict):
                    existing = loaded
        except Exception:
            existing = {}

        now = datetime.datetime.now()
        cache_data = dict(existing)
        cache_data["last_time"] = self._current_week()
        cache_data["focus"] = role
        cache_data["main_update_at"] = now.timestamp()
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        self.logger.info("缓存保存成功")
