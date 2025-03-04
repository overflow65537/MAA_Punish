import time
from typing import Callable, Optional, Union

from maa.job import Job, JobWithResult
from pathlib import Path
import sys

# 获取当前文件的绝对路径
current_file = Path(__file__).resolve()

# 定义可能的项目根目录相对路径
MFW_root = current_file.parent.parent.parent.parent.joinpath("MFW_resource")
MAA_Punish_root = current_file.parent.parent.parent.parent.parent.parent.joinpath("Bundles")
assets_root = current_file.parent.parent.parent.parent.parent.joinpath("assets")
if MFW_root.exists():
    project_root = MFW_root
    print("MFW root")
elif MAA_Punish_root.exists():
    project_root = MAA_Punish_root.joinpath("MAA_Punish")
    print("MAA_Punish root")
elif assets_root.exists():
    project_root = assets_root
    print("assets root")

print(project_root)

# 添加项目根目录到sys.path
sys.path.append(str(project_root))
from custom.action.tool import ActionStatusEnum, GameActionEnum


class JobExecutor:
    """增强版Job状态检查执行器(支持任务重试)"""

    def __init__(
        self,
        job_factory: Callable[[], Union[Job, JobWithResult, Callable]],
        action_enum: GameActionEnum,
        status_enum: ActionStatusEnum = ActionStatusEnum.DONE,
        success_enum: ActionStatusEnum = ActionStatusEnum.SUCCEEDED,
    ):
        """
        :param job_factory: 生成Job实例的工厂函数
        :param action_enum: 动作(用于日志输出)
        :param status_enum: 要监控的状态属性(默认为'DONE')
        :param success_enum: 成功判断属性(默认为'SUCCEEDED')
        """
        self.job_factory = job_factory
        self.action_name = action_enum.name.lower()
        self._status_check_attr = status_enum.name.lower()
        self._success_check_attr = success_enum.name.lower()
        self._current_job: Union[Job, JobWithResult] = None  # 当前监控的Job实例

    def _create_checker(self, job: Union[Job, JobWithResult], attr: str) -> Callable[[], bool]:
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
                    print(f"[尝试] {self.action_name} 第{attempt}次执行")
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

    def get_result(self) -> Optional[object]:
        """安全获取执行结果"""
        if isinstance(self._current_job, JobWithResult):
            try:
                return self._current_job.get()
            except Exception as e:
                print(f"[警告] 结果获取失败: {str(e)}")
        return None

    def _log_success(self, verbose: bool):
        """成功日志"""
        if not verbose:
            return
        # 直接使用Status的字符串表示
        status = str(self._current_job)
        result = self.get_result()
        result_str = f" | 结果: {result}" if result is not None else ""
        print(f"[成功] {self.action_name} | 状态: {status}{result_str}")

    def _log_failure(self, verbose: bool):
        """失败日志"""
        if verbose:
            status = str(self._current_job)
            print(f"[失败] {self.action_name} | 状态: {status}")

    def _log_timeout(self, timeout: float, verbose: bool):
        """超时日志"""
        if verbose:
            status = str(self._current_job)
            print(f"[超时] {self.action_name} | 等待超过 {timeout}秒 | 最后状态: {status}")

    def _log_error(self, error: Exception, verbose: bool):
        """异常日志"""
        if verbose:
            status = str(self._current_job) if self._current_job else "无有效任务"
            print(f"[异常] {self.action_name} | 状态: {status} | 错误: {str(error)}")
