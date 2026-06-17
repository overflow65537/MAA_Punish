"""
分辨率检查器

在任务开始时检查模拟器分辨率是否为 16:9，如果不是则停止任务并输出警告。
"""

from maa.event_sink import NotificationType
from maa.tasker import Tasker, TaskerEventSink
from agent.logger_component import LoggerComponent

logger_component = LoggerComponent(__name__)
logger = logger_component.logger


class AspectRatioChecker(TaskerEventSink):
    """
    分辨率检查器
    在任务开始时检查设备分辨率是否为 16:9
    """

    SWITCH_ACCOUNT_REQUIRED_RESOLUTION = (1280, 720)
    # 允许常见分辨率四舍五入带来的 1 像素误差，例如 1366x768。
    MAX_ASPECT_RATIO_PIXEL_ERROR = 1

    def __init__(self):
        super().__init__()

    def on_tasker_task(
        self,
        tasker: Tasker,
        noti_type: NotificationType,
        detail: TaskerEventSink.TaskerTaskDetail,
    ):
        if noti_type != NotificationType.Starting:
            return

        if detail.entry == "MaaTaskerPostStop":
            logger.debug("收到 PostStop 事件，跳过分辨率检查")
            return

        logger.debug(
            f"任务开始前检查分辨率 - task_id: {detail.task_id}, entry: {detail.entry}"
        )

        controller = tasker.controller
        if controller is None:
            logger.error("无法获取控制器")
            return

        width, height = self.get_controller_resolution(
            controller, ensure_screencap=True
        )
        if width <= 0 or height <= 0:
            logger.error("无法获取控制器实际未缩放分辨率")
            tasker.post_stop()
            return

        logger.debug(f"实际未缩放分辨率: {self.format_resolution(width, height)}")

        if not self.is_aspect_ratio_16x9(width, height):
            actual_ratio = self.calculate_aspect_ratio(width, height)
            logger.error(
                f"🚨 分辨率比例不匹配！任务已停止。"
                f"当前: {self.format_resolution(width, height)} (比例: {actual_ratio:.4f})，"
                f"请将模拟器分辨率设置为 16:9任意分辨率"
            )

            tasker.post_stop()

        else:
            logger.debug(
                f"分辨率检查通过: {self.format_resolution(width, height)} (16:9)"
            )

    @staticmethod
    def get_controller_resolution(
        controller, ensure_screencap: bool = True
    ) -> tuple[int, int]:
        if controller is None:
            return (0, 0)

        if ensure_screencap:
            try:
                img = controller.cached_image
                if img is None:
                    controller.post_screencap().wait().get()
            except Exception as exc:
                logger.warning(f"初始化分辨率失败: {exc}")

        try:
            width, height = controller.resolution
        except Exception as exc:
            logger.warning(f"获取控制器分辨率失败: {exc}")
            return (0, 0)

        return (int(width), int(height))

    @staticmethod
    def format_resolution(width: int, height: int) -> str:
        return f"{width}x{height}"

    @classmethod
    def is_aspect_ratio_16x9(cls, width: int, height: int) -> bool:
        """检查尺寸是否约为 16:9（含横屏与竖屏）。"""
        if width <= 0 or height <= 0:
            return False

        long_side = max(width, height)
        short_side = min(width, height)
        error = abs(long_side * 9 - short_side * 16)

        return error <= 16 * cls.MAX_ASPECT_RATIO_PIXEL_ERROR

    @staticmethod
    def calculate_aspect_ratio(width: int, height: int) -> float:
        """返回较大边与较小边的比值，统一横竖屏方向。"""
        w = float(width)
        h = float(height)
        if w > h:
            return w / h
        return h / w
