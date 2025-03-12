import os
import sys
import time
from pathlib import Path
from typing import Callable, Optional

from maa.job import Job

# 获取当前文件的绝对路径
current_file = Path(__file__).resolve()

# 定义可能的项目根目录相对路径
root_paths = [
    current_file.parent.parent.parent.parent.joinpath("MFW_resource"),
    current_file.parent.parent.parent.parent.parent.parent.joinpath("Bundles").joinpath("MAA_Punish"),
    current_file.parent.parent.parent.parent.parent.joinpath("assets"),
]

# 确定项目根目录
project_root = next((path for path in root_paths if path.exists()), None)
if project_root:
    if project_root == current_file.parent.parent.parent.parent.joinpath("MFW_resource"):
        project_root = current_file.parent.parent.parent.parent
    print(f"项目根目录: {project_root}")
    # 添加项目根目录到sys.path
    sys.path.append(str(project_root))
    from custom.action.tool import ActionStatusEnum, GameActionEnum
    from custom.action.tool.Logger import Logger
else:
    from assets.custom.action.tool import ActionStatusEnum, GameActionEnum
    from assets.custom.action.tool.Logger import Logger




class JobExecutor:
    """增强版Job状态检查执行器(支持任务重试)"""

    def __init__(
        self,
        job_factory: callable,
        action_enum: GameActionEnum,
        status_enum: ActionStatusEnum = ActionStatusEnum.DONE,
        success_enum: ActionStatusEnum = ActionStatusEnum.SUCCEEDED,
        role_name: str = None,
    ):
        """
        :param job_factory: 生成Job实例的工厂函数
        :param action_enum: 动作(用于日志输出)
        :param status_enum: 要监控的状态属性(默认为'DONE')
        :param success_enum: 成功判断属性(默认为'SUCCEEDED')
        """
        self.job_factory = job_factory
        self.action_name = action_enum.name.lower()
        self.action_name_zh = action_enum.value
        self._status_check_attr = status_enum.name.lower()
        self._success_check_attr = success_enum.name.lower()
        self._current_job: Optional[Job] = None  # 当前监控的Job实例
        self.role_name = role_name or "未知角色"
        self._log_file_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "action_log", self.role_name, "job.log"
        )  # 日志文件路径
        self._logger = Logger(name=f"{self.role_name}_Job", log_file=self._log_file_path)  # 日志实例

    def _create_checker(self, job: Optional[Job], attr: str) -> Callable[[], bool]:
        """创建属性检查闭包"""
        return lambda: getattr(job, attr)

    def execute(self, timeout: float = 3, interval: float = 0.1, max_retries: int = 2, verbose: bool = True) -> bool:
        """
        执行任务并监控状态(每次重试创建新Job实例)
        :param timeout: 超时时间(秒)
        :param interval: 轮询间隔(秒)
        :param max_retries: 最大重试次数
        :param verbose: 是否打印日志
        :return: 是否成功完成
        """

        for attempt in range(1, max_retries + 1):
            try:
                if verbose:
                    self._logger.info(f"[尝试] {self.action_name_zh} 第{attempt}次执行")
                self._current_job = self.job_factory()

                status_check = self._create_checker(self._current_job, self._status_check_attr)
                success_check = self._create_checker(self._current_job, self._success_check_attr)

                timeout_at = time.time() + timeout
                last_log_time = 0  # 用于控制日志频率

                while time.time() < timeout_at:
                    if status_check():  # 检测到任务完成
                        if success_check():
                            self._log_success(verbose)
                            return True
                        else:
                            self._log_failure(verbose)
                            break  # 跳出当前重试循环

                    # 每秒打印一次等待日志
                    if verbose and (time.time() - last_log_time >= 1.0):
                        elapsed = int(time.time() - (timeout_at - timeout))
                        print(f"[等待] {self.action_name} - 已等待 {elapsed}s")
                        last_log_time = time.time()

                    time.sleep(interval)
                else:  # 正常循环结束(即超时)
                    self._log_timeout(timeout, verbose)

            except Exception as e:
                self._log_error(e, verbose)
                if attempt == max_retries:
                    return False
                time.sleep(2**attempt)  # 指数退避策略

        return False  # 所有重试均失败

    def _log_success(self, verbose: bool):
        """成功日志"""
        if verbose:
            status = str(self._current_job.succeeded)
            self._logger.info(f"{self.action_name_zh} | 状态: {status}")

    def _log_failure(self, verbose: bool):
        """失败日志"""
        if verbose:
            status = str(self._current_job.succeeded)
            self._logger.warning(f"{self.action_name_zh} | 状态: {status}")

    def _log_timeout(self, timeout: float, verbose: bool):
        """超时日志"""
        if verbose:
            status = str(self._current_job.succeeded)
            self._logger.warning(f"{self.action_name_zh} | 等待超过 {timeout}秒 | 最后状态: {status}")

    def _log_error(self, error: Exception, verbose: bool):
        """异常日志"""
        if verbose:
            status = str(self._current_job.succeeded) if self._current_job else "无有效任务"
            self._logger.exception(f"{self.action_name_zh} | 状态: {status} | 错误: {str(error)}")
