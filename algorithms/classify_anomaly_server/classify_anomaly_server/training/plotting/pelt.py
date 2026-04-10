"""PELT 变点检测专属绘图实现."""

from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .common import save_and_log_figure


Array1D = NDArray[Any]


def _extract_positive_ranges(labels: Array1D) -> List[Tuple[int, int]]:
    """提取标签中连续正样本区间."""
    ranges: List[Tuple[int, int]] = []
    start: Optional[int] = None

    for idx, value in enumerate(labels):
        if value == 1 and start is None:
            start = idx
        elif value != 1 and start is not None:
            ranges.append((start, idx - 1))
            start = None

    if start is not None:
        ranges.append((start, len(labels) - 1))

    return ranges


def _match_changepoints(
    changepoints: Array1D,
    true_labels: Array1D,
    tolerance: int,
) -> Dict[str, Any]:
    """按容忍窗口匹配预测变点与真实变点窗口中心."""
    true_ranges = _extract_positive_ranges(true_labels)
    true_centers = [int(round((start + end) / 2)) for start, end in true_ranges]

    matched_pairs: List[Dict[str, int]] = []
    used_true: set[int] = set()
    unmatched_predictions: List[int] = []

    for pred in sorted(int(cp) for cp in np.asarray(changepoints, dtype=int)):
        candidates = [
            (abs(pred - center), idx, center)
            for idx, center in enumerate(true_centers)
            if idx not in used_true and abs(pred - center) <= tolerance
        ]
        if not candidates:
            unmatched_predictions.append(pred)
            continue

        distance, true_idx, center = min(candidates, key=lambda item: item[0])
        used_true.add(true_idx)
        matched_pairs.append(
            {
                "predicted": pred,
                "true_center": center,
                "distance": int(distance),
            }
        )

    unmatched_true = [
        center for idx, center in enumerate(true_centers) if idx not in used_true
    ]

    return {
        "true_ranges": true_ranges,
        "true_centers": true_centers,
        "matched_pairs": matched_pairs,
        "unmatched_predictions": unmatched_predictions,
        "unmatched_true": unmatched_true,
    }


def plot_pelt_changepoint_results(
    timestamps: Union[pd.DatetimeIndex, Array1D],
    values: Array1D,
    changepoints: Array1D,
    predictions: Array1D,
    true_labels: Optional[Array1D] = None,
    event_window: int = 1,
    title: str = "PELT 变点检测结果",
    artifact_name: str = "pelt_changepoint_plot",
    metrics: Optional[Dict[str, float]] = None,
) -> str:
    """绘制 PELT 专属变点/事件窗口图并上传到 MLflow."""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    if isinstance(timestamps, pd.DatetimeIndex):
        index = timestamps
    else:
        index = np.arange(len(values))

    ax1 = axes[0]
    ax1.plot(
        index, values, color="#2E86AB", linewidth=1.5, alpha=0.85, label="原始数据"
    )

    for idx, changepoint in enumerate(changepoints):
        if 0 <= changepoint < len(values):
            ax1.axvline(
                x=index[changepoint],
                color="#F24236",
                linestyle="--",
                linewidth=1.5,
                alpha=0.85,
                label="检测到的变点" if idx == 0 else None,
            )

    if true_labels is not None:
        true_mask = true_labels == 1
        if true_mask.any():
            ax1.scatter(
                np.asarray(index)[true_mask],
                values[true_mask],
                color="#06A77D",
                s=45,
                marker="x",
                linewidths=2,
                alpha=0.85,
                label="真实异常窗口",
            )

    ax1.set_title(f"{title} - 原始序列与变点", fontsize=12, fontweight="bold")
    ax1.set_ylabel("数值", fontsize=10)
    ax1.legend(loc="best", framealpha=0.9, fontsize=9)
    ax1.grid(True, alpha=0.3, linestyle="--")

    ax2 = axes[1]
    ax2.step(
        index,
        predictions,
        where="mid",
        color="#9D4EDD",
        linewidth=1.5,
        label="事件窗口标记",
    )
    ax2.fill_between(
        index,
        0,
        1,
        where=predictions == 1,
        color="#F24236",
        alpha=0.2,
        label="预测窗口",
    )

    for idx, changepoint in enumerate(changepoints):
        if 0 <= changepoint < len(values):
            start = max(0, changepoint - event_window)
            end = min(len(values) - 1, changepoint + event_window)
            ax2.axvspan(
                index[start],
                index[end],
                color="#F6BD60",
                alpha=0.15,
                label="变点影响窗口" if idx == 0 else None,
            )

    ax2.set_title("PELT 事件窗口视图", fontsize=12, fontweight="bold")
    ax2.set_xlabel("时间", fontsize=10)
    ax2.set_ylabel("窗口标签", fontsize=10)
    ax2.set_ylim(-0.05, 1.05)
    ax2.legend(loc="best", framealpha=0.9, fontsize=9)
    ax2.grid(True, alpha=0.3, linestyle="--")

    if metrics:
        display_metrics = {
            k: v
            for k, v in metrics.items()
            if not k.startswith("_") and isinstance(v, (int, float))
        }
        metrics_text = "\n".join([f"{k}: {v:.4f}" for k, v in display_metrics.items()])
        ax1.text(
            0.02,
            0.98,
            metrics_text,
            transform=ax1.transAxes,
            fontsize=9,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

    plt.tight_layout()
    return save_and_log_figure(artifact_name, "PELT 变点结果图已上传到 MLflow")


def plot_pelt_changepoint_alignment(
    timestamps: Union[pd.DatetimeIndex, Array1D],
    values: Array1D,
    changepoints: Array1D,
    true_labels: Array1D,
    tolerance: int,
    title: str = "PELT 变点对齐分析",
    artifact_name: str = "pelt_changepoint_alignment",
) -> str:
    """绘制 PELT 预测变点与真实变点窗口的对齐图."""
    if isinstance(timestamps, pd.DatetimeIndex):
        index = timestamps
    else:
        index = np.arange(len(values))

    alignment = _match_changepoints(changepoints, true_labels, tolerance)
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    ax1 = axes[0]
    ax1.plot(
        index, values, color="#2E86AB", linewidth=1.5, alpha=0.85, label="原始数据"
    )

    for idx, (start, end) in enumerate(alignment["true_ranges"]):
        ax1.axvspan(
            index[start],
            index[end],
            color="#06A77D",
            alpha=0.18,
            label="真实变点窗口" if idx == 0 else None,
        )

    for idx, cp in enumerate(np.asarray(changepoints, dtype=int)):
        if 0 <= cp < len(values):
            ax1.axvline(
                index[cp],
                color="#F24236",
                linestyle="--",
                linewidth=1.5,
                alpha=0.85,
                label="预测变点" if idx == 0 else None,
            )

    ax1.set_title(f"{title} - 序列与窗口", fontsize=12, fontweight="bold")
    ax1.set_ylabel("数值", fontsize=10)
    ax1.legend(loc="best", framealpha=0.9, fontsize=9)
    ax1.grid(True, alpha=0.3, linestyle="--")

    ax2 = axes[1]
    pred_y = np.full(len(changepoints), 1.0)
    true_y = np.full(len(alignment["true_centers"]), 0.0)

    if len(alignment["true_centers"]) > 0:
        ax2.scatter(
            np.asarray(index)[alignment["true_centers"]],
            true_y,
            color="#06A77D",
            s=90,
            marker="o",
            label="真实窗口中心",
            zorder=4,
        )
    if len(changepoints) > 0:
        ax2.scatter(
            np.asarray(index)[np.asarray(changepoints, dtype=int)],
            pred_y,
            color="#F24236",
            s=90,
            marker="^",
            label="预测变点",
            zorder=5,
        )

    for pair in alignment["matched_pairs"]:
        pred = pair["predicted"]
        true_center = pair["true_center"]
        ax2.plot(
            [index[true_center], index[pred]],
            [0.0, 1.0],
            color="#9D4EDD",
            linewidth=1.2,
            alpha=0.7,
        )
        mid_x = index[pred]
        if hasattr(mid_x, "to_pydatetime"):
            mid_x = index[pred]
        ax2.text(
            mid_x,
            0.52,
            f"\u0394={pair['distance']}",
            fontsize=8,
            ha="left",
            va="center",
            color="#5A189A",
        )

    summary_text = "\n".join(
        [
            f"匹配数: {len(alignment['matched_pairs'])}",
            f"漏检数: {len(alignment['unmatched_true'])}",
            f"误检数: {len(alignment['unmatched_predictions'])}",
            f"容忍窗口: \u00b1{tolerance}",
        ]
    )
    ax2.text(
        0.02,
        0.98,
        summary_text,
        transform=ax2.transAxes,
        fontsize=9,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
    )

    ax2.set_title(f"{title} - 对齐关系", fontsize=12, fontweight="bold")
    ax2.set_xlabel("时间", fontsize=10)
    ax2.set_yticks([0.0, 1.0])
    ax2.set_yticklabels(["真实中心", "预测变点"])
    ax2.set_ylim(-0.4, 1.4)
    ax2.legend(loc="best", framealpha=0.9, fontsize=9)
    ax2.grid(True, alpha=0.3, linestyle="--")

    plt.tight_layout()
    return save_and_log_figure(artifact_name, "PELT 变点对齐图已上传到 MLflow")


def plot_pelt_hyperopt_trajectory(
    trial_history: List[Dict[str, Any]],
    title: str = "PELT 超参数搜索轨迹",
    artifact_name: str = "pelt_hyperopt_trajectory",
) -> str:
    """绘制 PELT 超参数搜索得分轨迹图."""
    if not trial_history:
        return ""

    trials = [int(item["trial"]) for item in trial_history]
    scores = [float(item["score"]) for item in trial_history]
    best_so_far = np.maximum.accumulate(scores)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(
        trials,
        scores,
        marker="o",
        linewidth=1.5,
        color="#2E86AB",
        label="trial score",
    )
    ax.plot(trials, best_so_far, linewidth=2.0, color="#F24236", label="best so far")
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel("Trial", fontsize=10)
    ax.set_ylabel("Score", fontsize=10)
    ax.legend(loc="best", framealpha=0.9, fontsize=9)
    ax.grid(True, alpha=0.3, linestyle="--")

    plt.tight_layout()
    return save_and_log_figure(artifact_name, "PELT 超参数搜索轨迹图已上传到 MLflow")


def plot_pelt_pen_score_changepoints(
    trial_history: List[Dict[str, Any]],
    title: str = "PELT pen-score-num_changepoints 关系图",
    artifact_name: str = "pelt_pen_score_num_changepoints",
) -> str:
    """绘制 pen、score 与变点数量之间的关系图."""
    if not trial_history:
        return ""

    pens = np.array([float(item["pen"]) for item in trial_history], dtype=float)
    scores = np.array([float(item["score"]) for item in trial_history], dtype=float)
    num_cps = np.array(
        [float(item["num_changepoints"]) for item in trial_history], dtype=float
    )

    fig, ax1 = plt.subplots(figsize=(10, 6))
    scatter = ax1.scatter(
        pens,
        scores,
        c=num_cps,
        cmap="viridis",
        s=90,
        alpha=0.85,
        edgecolors="black",
        linewidths=0.4,
    )
    ax1.set_xlabel("pen", fontsize=10)
    ax1.set_ylabel("score", fontsize=10)
    ax1.set_title(title, fontsize=12, fontweight="bold")
    ax1.grid(True, alpha=0.3, linestyle="--")

    unique_pens = sorted(set(pens.tolist()))
    avg_num_cps = [float(num_cps[pens == pen].mean()) for pen in unique_pens]
    ax2 = ax1.twinx()
    ax2.plot(
        unique_pens,
        avg_num_cps,
        color="#F24236",
        marker="s",
        linewidth=2,
        label="avg num_changepoints",
    )
    ax2.set_ylabel("avg num_changepoints", fontsize=10)

    cbar = plt.colorbar(scatter, ax=ax1)
    cbar.set_label("num_changepoints", rotation=270, labelpad=15, fontsize=10)

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    if handles2:
        ax1.legend(
            handles1 + handles2,
            labels1 + labels2,
            loc="best",
            framealpha=0.9,
            fontsize=9,
        )

    plt.tight_layout()
    return save_and_log_figure(
        artifact_name, "PELT pen-score-num_changepoints 图已上传到 MLflow"
    )
