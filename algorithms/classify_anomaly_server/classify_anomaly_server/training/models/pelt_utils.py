"""PELT changepoint 到点级异常窗口的映射工具。"""

from importlib import import_module
from typing import Iterable

import numpy as np


def breakpoints_to_changepoints(breakpoints: Iterable[int], length: int) -> list[int]:
    """将 ruptures 返回的断点转换为真实 changepoint 索引。"""
    changepoints: list[int] = []
    for breakpoint in breakpoints:
        if 0 <= breakpoint < length:
            changepoints.append(int(breakpoint))
    return changepoints


def detect_changepoints(
    signal: np.ndarray,
    *,
    cost_model: str,
    min_size: int,
    jump: int,
    pen: float,
) -> list[int]:
    """运行 PELT 并返回有效 changepoint 索引。"""
    if len(signal) == 0 or len(signal) < max(2, min_size * 2):
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
