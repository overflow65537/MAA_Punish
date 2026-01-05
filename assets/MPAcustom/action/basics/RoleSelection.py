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
import logging
import os
from datetime import datetime, timedelta
import numpy


from MPAcustom.action.tool.LoadSetting import ROLE_ACTIONS


class RoleSelection(CustomAction):
    def __init__(self):
        super().__init__()
        self.logger = self._setup_logger()
        self._clear_old_logs()

    def _setup_logger(self):
        debug_dir = "debug"
        os.makedirs(debug_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d")
        log_file_name = f"custom_{timestamp}.log"
        log_file_path = os.path.join(debug_dir, log_file_name)

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        logger.propagate = False

        file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        return logger

    def __del__(self):
        """清理日志记录器资源"""
        try:
            if hasattr(self, "logger") and self.logger:
                # 安全地关闭所有处理器
                for handler in self.logger.handlers[:]:
                    try:
                        handler.close()
                    except:
                        pass
                    self.logger.removeHandler(handler)
        except:
            # 避免在析构函数中抛出异常
            pass

    def _clear_old_logs(self):
        debug_dir = "debug"
        if not os.path.isdir(debug_dir):
            return

        three_days_ago = datetime.now() - timedelta(days=3)
        for root, dirs, files in os.walk(debug_dir):
            for file in files:
                if file.startswith("custom_") and file.endswith(".log"):
                    try:
                        timestamp_str = file.split("_")[1].split(".")[0]
                        file_time = datetime.strptime(timestamp_str, "%Y%m%d")
                        if file_time < three_days_ago:
                            file_path = os.path.join(root, file)
                            os.remove(file_path)
                            self.logger.info(f"已删除过期日志文件: {file_path}")
                    except Exception as e:
                        self.logger.error(f"处理文件 {file} 时出错: {e}")

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        condition = json.loads(argv.custom_action_param)
        if condition is None:
            condition = {}
        role = {}

        role_dict = ROLE_ACTIONS.copy()
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
            if not condition.get("cage") and condition.get("pick", "") in role.keys():
                break
            context.run_action("滑动_选人")

        role_weight = self.calculate_weight(role, condition)
        self.logger.info(f"条件: {condition}")
        self.logger.info(f"角色权重: {role_weight}")
        print(f"角色权重: {role_weight}")
        if not (not condition.get("cage") and condition.get("pick", "") in role.keys()):
            for _ in range(int(condition.get("max_try", 5))):
                if context.tasker.stopping:
                    return CustomAction.RunResult(success=True)
                context.run_action("反向滑动_选人")
        # 找出权重最高的key
        selected_role = max(role_weight.items(), key=lambda x: x[1])[0]
        for role_name, weight in role_weight.items():
            self.send_msg(context, f"角色: {role_name}, 权重: {weight}")
        if condition.get("pick") and condition.get("pick") not in role_weight.keys():
            self.send_msg(
                context,
                f"未检测到 {condition.get('pick')},选中权重最高的角色 {selected_role}",
            )

        nonselected_roles = False
        if role_weight[selected_role] == 0:
            self.logger.info(f"角色次数全为0")
            nonselected_roles = True
        else:
            self.logger.info(f"选择角色: {selected_role}")

        target = None
        images = []
        target_x, target_y = None, None
        for _ in range(int(condition.get("max_try", 5))):
            if context.tasker.stopping:
                return CustomAction.RunResult(success=True)
            image = context.tasker.controller.post_screencap().wait().get()
            images.append(image)
            if nonselected_roles and condition.get("cage"):
                # 没有对应人物,且是囚笼模式,随便选一个带次数的
                print("没有对应人物,且是囚笼模式,随便选一个带次数的")
                target = context.run_recognition(
                    "选择人物",
                    image,
                    {
                        "选择人物": {
                            "recognition": {
                                "type": "ColorMatch",
                                "param": {
                                    "roi": [72, 69, 140, 521],
                                    "upper": [53, 175, 248],
                                    "lower": [53, 175, 248],
                                    "connected": True,
                                    "count": 10,
                                },
                            }
                        }
                    },
                )
                if target and target.hit:
                    if isinstance(target.best_result, ColorMatchResult):
                        context.tasker.controller.post_click(
                            target.best_result.box[0], target.best_result.box[1]
                        )
                        context.run_task("编入队伍")
                        return CustomAction.RunResult(success=True)
            elif nonselected_roles:
                # 没有对应人物,随便选一个带次数的
                print("没有对应人物,随便选一个带次数的")
                context.run_task("编入队伍")
                return CustomAction.RunResult(success=True)
            else:
                # 有对应人物,选对应人物
                print(f"有对应人物,选对应人物: {selected_role}")
                target = context.run_recognition(
                    "选择人物",
                    image,
                    {
                        "选择人物": {
                            "recognition": {
                                "param": {
                                    "template": role_dict[
                                        selected_role.replace("[试用]", "")
                                    ]["template"],
                                    "threshold": [0.7]
                                    * len(
                                        role_dict[selected_role.replace("[试用]", "")][
                                            "template"
                                        ]
                                    ),
                                },
                            },
                        }
                    },
                )

            if (
                target
                and target.hit
                and isinstance(target.best_result, TemplateMatchResult)
            ):
                print(
                    f"找到对应人物: {selected_role},数量: {len(target.filtered_results)}"
                )
                for result in target.filtered_results:
                    print(f"对应人物位置: {result.box}")
                    trial_reco = context.run_recognition(
                        "识别试用角色",
                        image,
                        {
                            "识别试用角色": {
                                "recognition": {"param": {"roi": result.box}},
                            }
                        },
                    )
                    if trial_reco and ("[试用]" in selected_role) == trial_reco.hit:
                        print(f"对应人物是否是试用角色: {trial_reco.hit}")
                        target_x, target_y = (
                            result.box[0] + result.box[2] // 2,
                            result.box[1] + result.box[3] // 2,
                        )

                if target_x and target_y:
                    context.tasker.controller.post_click(target_x, target_y).wait()
                    context.run_task("编入队伍")
                    self.logger.info(f"选择角色成功: {selected_role}")
                    return CustomAction.RunResult(success=True)
            context.run_action("滑动_选人")
        if not (target and target.hit):
            for i, img in enumerate(images, 1):
                self.save_screenshot(img, f"未找到角色_尝试{i}")
            self.logger.info(f"选择角色失败: {selected_role}")
            self.send_msg(context, f"未找到角色 {selected_role},退出任务")
            context.run_task("返回主菜单")
            context.override_next(argv.node_name, ["停止任务"])
            context.override_pipeline(
                {
                    "停止任务": {
                        "focus": {
                            "Node.Recognition.Succeeded": f"未找到角色 {selected_role},退出任务"
                        }
                    }
                }
            )

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
                        cage_result = context.run_recognition(
                            entry="识别囚笼次数",
                            image=image,
                            pipeline_override={
                                "识别囚笼次数": {
                                    "recognition": {
                                        "param": {"roi": role_reco.box},
                                    }
                                }
                            },
                        )
                        role[display_name]["cage"] = bool(
                            cage_result and cage_result.hit
                        )
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
            has_count = info.get("cage", True)
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
            ) * (1 if has_count else 0)

            # 6. 最终权重 = 基础权重 + 选中加成
            w = base_weight

            self.logger.debug(
                f"{role_name}: 战力={power_weight}, 属性分={attribute_weight}, 代数分={generation_weight}, "
                f"精通分={master_level_weight}, 选中加成={pick_bonus}, 基础权重={base_weight}, 最终权重={w}"
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
