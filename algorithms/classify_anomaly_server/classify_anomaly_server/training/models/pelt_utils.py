"""PELT changepoint 到点级异常窗口的映射工具。"""

from importlib import import_module
from typing import Iterable

import numpy as np
from numpy.typing import NDArray
from loguru import logger


def breakpoints_to_changepoints(breakpoints: Iterable[int], length: int) -> list[int]:
    """将 ruptures 返回的断点转换为真实 changepoint 索引。"""
    changepoints: list[int] = []
    for breakpoint in breakpoints:
        if 0 <= breakpoint < length:
            changepoints.append(int(breakpoint))
    return changepoints


def detect_changepoints(
    signal: NDArray[np.float64],
    *,
    cost_model: str,
    min_size: int,
    jump: int,
    pen: float,
) -> list[int]:
    """运行 PELT 并返回有效 changepoint 索引。"""
    if len(signal) == 0 or len(signal) < max(2, min_size * 2):
        logger.warning(
            f"PELT 跳过变点检测: signal_length={len(signal)} < required_min_length={max(2, min_size * 2)} (min_size={min_size}), returning empty changepoints"
        )
        return []

    rpt = import_module("ruptures")
    algo = rpt.Pelt(model=cost_model, min_size=min_size, jump=jump)
    breakpoints = algo.fit_predict(signal, pen=pen)
    return breakpoints_to_changepoints(breakpoints, len(signal))


def event_window_scores(
    length: int,
    changepoints: Iterable[int],
    event_window: int,
    score: float = 1.0,
) -> np.ndarray[tuple[int], np.dtype[np.float64]]:
    """将 changepoint 展开成边界裁剪后的对称点级分数。"""
    scores = np.zeros(length, dtype=float)
    if length <= 0:
        return scores

    for changepoint in changepoints:
        start = max(0, int(changepoint) - event_window)
        end = min(length - 1, int(changepoint) + event_window)
        scores[start : end + 1] = np.maximum(scores[start : end + 1], score)

    return scores


def project_changepoints_to_point_scores(
    length: int,
    changepoints: Iterable[int],
    event_window: int,
) -> NDArray[np.float64]:
    """将 changepoint 映射为点级二值窗口分数。"""
    return event_window_scores(
        length=length,
        changepoints=changepoints,
        event_window=event_window,
    )


def project_changepoints_to_point_labels(
    length: int,
    changepoints: Iterable[int],
    event_window: int,
) -> NDArray[np.int_]:
    """将 changepoint 映射为点级二值标签。"""
    scores = project_changepoints_to_point_scores(
        length=length,
        changepoints=changepoints,
        event_window=event_window,
    )
    return (scores > 0).astype(int)
