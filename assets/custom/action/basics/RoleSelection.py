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
import sys
from pathlib import Path
import json
import logging
from pathlib import Path
import os
from datetime import datetime, timedelta
import numpy


# 获取当前文件的绝对路径
current_file = Path(__file__).resolve()
sys.path.append(str(current_file.parent.parent.parent.parent))
from custom.action.tool.LoadSetting import ROLE_ACTIONS


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

        target = None
        nonselected_roles = False
        if role_weight[selected_role] == 0:
            self.logger.info(f"角色次数全为0")
            nonselected_roles = True
        else:
            self.logger.info(f"选择角色: {selected_role}")

        target = None
        images = []
        for _ in range(int(condition.get("max_try", 5)) + 1):
            if context.tasker.stopping:
                return CustomAction.RunResult(success=True)
            image = context.tasker.controller.post_screencap().wait().get()
            images.append(image)
            if nonselected_roles and condition.get("cage"):
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
            elif nonselected_roles:
                context.run_task("编入队伍")
                return CustomAction.RunResult(success=True)
            else:
                target = context.run_recognition(
                    "选择人物",
                    image,
                    {
                        "选择人物": {
                            "recognition": {
                                "param": {
                                    "template": role_dict[selected_role]["template"],
                                    "threshold": [0.7]
                                    * len(role_dict[selected_role]["template"]),
                                },
                            },
                        }
                    },
                )
            if target and (
                isinstance(target.best_result, TemplateMatchResult)
                or isinstance(target.best_result, ColorMatchResult)
            ):
                context.tasker.controller.post_click(
                    target.best_result.box[0] + target.best_result.box[2] // 2,
                    target.best_result.box[1] + target.best_result.box[3] // 2,
                ).wait()
                context.run_task("编入队伍")
                self.logger.info(f"选择角色成功: {selected_role}")
                return CustomAction.RunResult(success=True)
            context.run_action("滑动_选人")
        if target is None:
            for i, img in enumerate(images, 1):
                self.save_screenshot(img, f"未找到角色_尝试{i}")
            self.logger.info(f"选择角色失败: {selected_role}")
            context.run_task("返回主菜单")
            context.override_next(argv.node_name, ["停止任务"])
            context.override_pipeline(
                {
                    "停止任务": {
                        "focus": {"Tasker.Task.Succeeded": f"未找到角色 {selected_role},退出任务"}
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
        for role_name, role_actions in role_actions.items():

            pipeline_override = {
                "识别角色": {
                    "recognition": {
                        "param": {"template": role_actions["template"]},
                    },
                }
            }

            result = context.run_recognition(
                entry="识别角色",
                image=image,
                pipeline_override=pipeline_override,
            )

            # 检查识别结果并提取box信息
            if result and isinstance(result.best_result, TemplateMatchResult):
                self.logger.info(f"识别到角色: {role_name}")
                role[role_name] = role_actions.copy().get("metadata", {})
                if cage:
                    role[role_name]["cage"] = bool(
                        context.run_recognition(entry="识别囚笼次数", image=image)
                    )
                if roguelike_3_mode == 1:
                    role[role_name]["master_level"] = bool(
                        context.run_recognition(
                            entry="识别精通等级",
                            image=image,
                            pipeline_override={
                                "识别精通等级": {
                                    "recognition": {
                                        "param": {
                                            "roi": result.best_result.box,
                                        },
                                    }
                                }
                            },
                        )
                    )

        return role

    # 计算权重
    def calculate_weight(self, role_info: dict, condition: dict[str, dict]) -> dict:
        """
        公式
        权重 = (( 属性分数 * 45) + (代数分数 * 2300) + (是否被选中 * 10000) + (是否精通等级没满 * 10000)) * 是否有次数
        """
        weight = {}

        for role_name, info in role_info.items():
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
            # 1. 属性分数
            attribute_weight = attribute_score * 45

            # 2. 代数分数
            generation_weight = element_score * 2300

            # 3. 精通等级分数
            master_level_weight = 10000 if is_master_level_not_full else 0

            # 4. 被选中加成
            pick_bonus = 10000 if is_pick else 0

            # 5. 基础权重 = (属性 + 代数 + 精通) * 是否有次数
            base_weight = (
                attribute_weight + generation_weight + master_level_weight + pick_bonus
            ) * (1 if has_count else 0)

            # 6. 最终权重 = 基础权重 + 选中加成
            w = base_weight

            self.logger.debug(
                f"{role_name}: 属性分={attribute_weight}, 代数分={generation_weight}, "
                f"精通分={master_level_weight}, 选中加成={pick_bonus}, 基础权重={base_weight}, 最终权重={w}"
            )
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
                "focus": {"Tasker.Task.Succeeded": msg}
            }
        }
        context.run_task(
            "发送消息_这是程序自动生成的node所以故意写的很长来防止某一天想不开用了这个名字导致报错",
            pipeline_override=msg_node,
        )
