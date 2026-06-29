"""信号球三消决策：纯算法，不依赖 Maa Framework。"""

from __future__ import annotations

import logging
from typing import Literal

BallColor = Literal["red", "blue", "yellow"] | None


def find_elimination_target(
    ball_list: list[BallColor],
    target_ball: str = "any",
    *,
    log: logging.Logger | None = None,
) -> int:
    """消球决策；正数为直接三消槽位，负数为移球策略，0 为无效。"""
    last_non_none_index = next(
        (i for i, x in enumerate(reversed(ball_list)) if x is not None), None
    )
    valid_length = (
        len(ball_list) - last_non_none_index
        if last_non_none_index is not None
        else 0
    )

    if log is not None:
        log.info("有效长度: %s", valid_length)

    if valid_length == 0:
        if log is not None:
            log.info("未找到有效操作")
        return 0

    is_any = target_ball == "any"

    if result := _check_triple_direct(
        ball_list, valid_length, is_any, target_ball, log=log
    ):
        return result

    if result := _check_combo_opportunity(
        ball_list, valid_length, is_any, target_ball, log=log
    ):
        return result

    if result := _check_any_triple(ball_list, log=log):
        return result

    return _select_non_empty(ball_list)


def _check_triple_direct(
    ball_list: list[BallColor],
    valid_length: int,
    is_any: bool,
    target: str,
    *,
    log: logging.Logger | None,
) -> int:
    for i in range(valid_length - 2):
        if (
            is_any and ball_list[i] == ball_list[i + 1] == ball_list[i + 2]
        ) or (
            not is_any
            and ball_list[i] == target
            and ball_list[i + 1] == target
            and ball_list[i + 2] == target
        ):
            if log is not None:
                log.info(
                    "第一优先级：%s三连消除",
                    "任意" if is_any else "目标",
                )
            return i + 1
    return 0


def _check_combo_opportunity(
    ball_list: list[BallColor],
    valid_length: int,
    is_any: bool,
    target: str,
    *,
    log: logging.Logger | None,
) -> int:
    candidate = 0
    for i in [
        idx for idx, x in enumerate(ball_list[:valid_length]) if x is not None
    ]:
        temp = ball_list[:i] + ball_list[i + 1 :]
        for j in range(min(len(temp) - 1, valid_length - 1)):
            if j <= len(temp) - 3:
                if (is_any and temp[j] == temp[j + 1] == temp[j + 2]) or (
                    not is_any and temp[j : j + 3] == [target] * 3
                ):
                    if log is not None:
                        log.info(
                            "第二优先级：可形成%s三连",
                            "任意" if is_any else "目标",
                        )
                    return -i

            if (is_any and temp[j] == temp[j + 1]) or (
                not is_any and temp[j] == target and temp[j + 1] == target
            ):
                if log is not None:
                    log.info(
                        "第二优先级：可形成%s二连",
                        "任意" if is_any else "目标",
                    )
                candidate = -i
    return candidate


def _check_any_triple(
    ball_list: list[BallColor],
    *,
    log: logging.Logger | None,
) -> int:
    for i in range(len(ball_list)):
        if ball_list[i] is None:
            continue
        temp = ball_list[:i] + ball_list[i + 1 :]
        for j in range(len(temp) - 2):
            if temp[j] is not None and temp[j] == temp[j + 1] == temp[j + 2]:
                if log is not None:
                    log.info("第三优先级：任意三连消除")
                return -i
    return 0


def _select_non_empty(ball_list: list[BallColor]) -> int:
    return -2 if ball_list[0] is None else -1
