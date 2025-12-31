"""
MAA_Punish
MAA_Punish 选择特定类型角色
作者:overflow65537
"""

import re
from maa.context import Context
from maa.custom_action import CustomAction
from maa.define import TemplateMatchResult, OCRResult, ColorMatchResult
import json
import logging
import os
from datetime import datetime, timedelta
import numpy


class RoleSelectionType(CustomAction):
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

        param = json.loads(argv.custom_action_param) or {}

        switch_item = 0
        while switch_item < 5:
            image = context.tasker.controller.post_screencap().wait().get()
            target_reco = context.run_recognition("检查支援类型角色", image)
            if target_reco and target_reco.hit:
                for reco in target_reco.filtered_results:
                    flag = context.run_recognition(
                        "检查支援类型角色是否被选中",
                        image,
                        {
                            "检查支援类型角色是否被选中": {
                                "recognition": {
                                    "param": {
                                        "roi": reco.box,
                                        "roi_offset": [-100, 60, 30, -10],
                                    },
                                }
                            }
                        },
                    )
                    if param.get("cage"):
                        cage_reco = context.run_recognition("识别囚笼次数_辅助", image)
                        if cage_reco and not cage_reco.hit:
                            continue

                    if flag and not flag.hit:
                        context.tasker.controller.post_click(
                            reco.box[0], reco.box[1]
                        ).wait()
                        context.run_task("编入队伍")
                        return CustomAction.RunResult(success=True)

            context.run_action("滑动_选人")
            switch_item += 1

        context.tasker.controller.post_click(210, 105).wait()
        context.run_task("编入队伍")
        return CustomAction.RunResult(success=True)
