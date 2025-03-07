import logging
import os
from logging.handlers import TimedRotatingFileHandler
from typing import Any, Dict, Optional, Union


class Logger:
    """
    通用日志记录类，支持日志轮转和保留指定天数内的日志

    Args:
        name: 日志记录器名称(默认"root")
        level: 全局日志级别(默认DEBUG)
        log_file: 日志文件路径(可选)
        log_format: 日志格式字符串(可选)
        console: 是否启用控制台输出(默认True)
        console_level: 控制台日志级别(可选，继承全局级别)
        file_level: 文件日志级别(可选，继承全局级别)
        backup_days: 保留日志文件的天数(默认3天)

    Example:
        >>> logger = Logger()
        >>> logger.info("Application started")
    """

    # DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DEFAULT_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

    def __init__(
        self,
        name: str = "root",
        level: Union[int, str] = logging.DEBUG,
        log_file: Optional[str] = None,
        log_format: Optional[str] = None,
        console: bool = True,
        console_level: Optional[Union[int, str]] = None,
        file_level: Optional[Union[int, str]] = None,
        backup_days: int = 3,
    ) -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        if self.logger.handlers:
            return

        formatter = logging.Formatter(log_format or self.DEFAULT_FORMAT)

        if console:
            self._add_stream_handler(formatter, console_level or level)

        if log_file:
            self._add_timed_rotating_file_handler(log_file, formatter, file_level or level, backup_days)

    def _add_stream_handler(self, formatter: logging.Formatter, level: Union[int, str]) -> None:
        """添加控制台日志处理器"""
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _add_timed_rotating_file_handler(
        self,
        file_path: str,
        formatter: logging.Formatter,
        level: Union[int, str],
        backup_days: int,
    ) -> None:
        """添加按时间轮转的文件日志处理器"""
        log_dir = os.path.dirname(file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        handler = TimedRotatingFileHandler(
            filename=file_path,
            when="midnight",
            interval=1,
            backupCount=backup_days,
            encoding="utf-8",
        )
        handler.setLevel(level)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def debug(self, msg: str, **kwargs: Dict[str, Any]) -> None:
        """记录DEBUG级别日志"""
        self.logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs: Dict[str, Any]) -> None:
        """记录INFO级别日志"""
        self.logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs: Dict[str, Any]) -> None:
        """记录WARNING级别日志"""
        self.logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs: Dict[str, Any]) -> None:
        """记录ERROR级别日志"""
        self.logger.error(msg, **kwargs)

    def exception(self, msg: str, **kwargs: Dict[str, Any]) -> None:
        """
        记录EXCEPTION级别日志
        自动添加异常信息，应在except块中使用
        """
        self.logger.exception(msg, **kwargs)

    def critical(self, msg: str, **kwargs: Dict[str, Any]) -> None:
        """记录CRITICAL级别日志"""
        self.logger.critical(msg, **kwargs)

    @property
    def handlers(self) -> list[logging.Handler]:
        """获取所有日志处理器"""
        return self.logger.handlers

    def add_handler(self, handler: logging.Handler) -> None:
        """添加自定义日志处理器"""
        self.logger.addHandler(handler)

    def set_level(self, level: Union[int, str]) -> None:
        """设置全局日志级别"""
        self.logger.setLevel(level)
