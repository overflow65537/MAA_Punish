import logging
import os
import sys
from datetime import datetime, timedelta

LOG_DIR = "debug"
RETENTION_DAYS = 3
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


class LoggerComponent:
    """提供统一的自定义日志记录器配置与过期日志清理功能。"""

    def __init__(self, name: str):
        self.logger = self._setup_logger(name)
        self._clear_old_logs()

    def __del__(self):
        self.close()

    def _setup_logger(self, name: str) -> logging.Logger:
        os.makedirs(LOG_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file_path = os.path.join(LOG_DIR, f"custom_{timestamp}.log")

        logger = logging.getLogger(f"MPAcustom.{name}")
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        logger.propagate = False

        file_handler = logging.FileHandler(
            log_file_path, mode="a", encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

        logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler(stream=sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(stream_handler)
        return logger

    def _clear_old_logs(self):
        if not os.path.isdir(LOG_DIR):
            return

        threshold = datetime.now() - timedelta(days=RETENTION_DAYS)
        for root, _, files in os.walk(LOG_DIR):
            for file_name in files:
                if not (file_name.startswith("custom_") and file_name.endswith(".log")):
                    continue
                try:
                    timestamp_str = file_name.split("_")[1].split(".")[0]
                    file_date = datetime.strptime(timestamp_str, "%Y%m%d")
                except Exception as exc:
                    self.logger.error(f"处理文件 {file_name} 时出错: {exc}")
                    continue
                if file_date < threshold:
                    file_path = os.path.join(root, file_name)
                    try:
                        os.remove(file_path)
                    except Exception as exc:
                        self.logger.error(
                            f"删除过期日志文件失败: {file_path} - {exc}"
                        )
                    else:
                        self.logger.info(f"已删除过期日志文件: {file_path}")

    def close(self):
        if not getattr(self, "logger", None):
            return
        for handler in self.logger.handlers[:]:
            try:
                handler.close()
            except Exception:
                pass
            finally:
                self.logger.removeHandler(handler)
