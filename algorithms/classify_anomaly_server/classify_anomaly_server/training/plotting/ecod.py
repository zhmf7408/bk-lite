"""ECOD 异常检测专属绘图实现."""

from typing import List, Optional, Sequence, cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger

from .common import save_and_log_figure


def plot_ecod_decomposition(
    model,
    X: pd.DataFrame,
    feature_names: List[str],
    sample_indices: Optional[Sequence[int]] = None,
    top_n: int = 10,
    title: str = "ECOD 异常分数分解",
    artifact_name: str = "ecod_decomposition",
) -> str:
    """绘制 ECOD 异常分数分解图.

    展示左尾（值过小）和右尾（值过大）的异常贡献，
    以及每个特征对异常分数的贡献度。

    Args:
        model: 训练好的 PyOD ECOD 模型实例 (需要已调用fit)
        X: 特征数据 DataFrame
        feature_names: 特征名称列表
        sample_indices: 要展示的样本索引列表，默认展示异常分数最高的top_n个
        top_n: 当sample_indices为None时，展示异常分数最高的N个样本
        title: 图表标题
        artifact_name: 保存的文件名

    Returns:
        保存的图片路径
    """
    try:
        # 检查模型是否有必要的属性
        if (
            not hasattr(model, "U_l")
            or not hasattr(model, "U_r")
            or not hasattr(model, "O")
        ):
            logger.warning("模型缺少 U_l/U_r/O 属性，跳过ECOD分解可视化")
            return ""

        # 计算异常分数
        scores = model.decision_function(X.values)

        # 选择要展示的样本
        selected_indices = sample_indices
        if selected_indices is None:
            # 选择异常分数最高的top_n个样本
            sample_indices_list = np.argsort(scores)[-top_n:][::-1].tolist()
        else:
            sample_indices_list = list(selected_indices)

        n_samples = len(sample_indices_list)
        n_features = len(feature_names)

        # 获取PyOD内部属性（训练时计算的）
        # 需要重新计算测试数据的左尾和右尾分数
        U_l = model.U_l[sample_indices_list, :] if len(model.U_l) == len(X) else None
        U_r = model.U_r[sample_indices_list, :] if len(model.U_r) == len(X) else None
        O = model.O[sample_indices_list, :] if len(model.O) == len(X) else None

        if U_l is None or U_r is None or O is None:
            logger.warning("无法获取样本的左尾/右尾分数，可能是训练集和测试集不匹配")
            return ""

        # 创建图表
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))

        # 上图: 左尾 vs 右尾分数堆叠柱状图
        ax1 = axes[0]

        # 计算每个样本的左尾和右尾总分
        left_tail_scores = U_l.sum(axis=1)
        right_tail_scores = U_r.sum(axis=1)
        total_scores = scores[sample_indices_list]

        x_pos = np.arange(n_samples)
        sample_labels = [f"样本 {idx}" for idx in sample_indices_list]

        # 堆叠柱状图
        bar_width = 0.6
        ax1.bar(
            x_pos,
            left_tail_scores,
            bar_width,
            label="左尾异常 (值过小)",
            color="#2E86AB",
            alpha=0.8,
        )
        ax1.bar(
            x_pos,
            right_tail_scores,
            bar_width,
            bottom=left_tail_scores,
            label="右尾异常 (值过大)",
            color="#F24236",
            alpha=0.8,
        )

        # 标注总分
        for i, (idx, score) in enumerate(zip(sample_indices_list, total_scores)):
            ax1.text(
                i,
                cast(float, score) + 0.05,
                f"{score:.2f}",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
            )

        ax1.set_xlabel("样本索引", fontsize=10)
        ax1.set_ylabel("异常分数", fontsize=10)
        ax1.set_title(f"{title} - 左尾 vs 右尾异常", fontsize=12, fontweight="bold")
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(sample_labels, rotation=45, ha="right", fontsize=8)
        ax1.legend(loc="best", framealpha=0.9)
        ax1.grid(True, alpha=0.3, axis="y")

        # 下图: 特征贡献热图
        ax2 = axes[1]

        # 使用O矩阵（每个特征的最大异常分数）
        feature_contributions = O.T  # 转置为 (n_features, n_samples)

        # 绘制热图
        im = ax2.imshow(
            feature_contributions,
            cmap="YlOrRd",
            aspect="auto",
            interpolation="nearest",
        )

        # 添加颜色条
        cbar = plt.colorbar(im, ax=ax2)
        cbar.set_label("特征异常分数", rotation=270, labelpad=15, fontsize=10)

        # 设置坐标轴
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(sample_labels, rotation=45, ha="right", fontsize=8)
        ax2.set_yticks(np.arange(n_features))
        ax2.set_yticklabels(feature_names, fontsize=8)

        # 在单元格中标注数值（仅对较大的值）
        for i in range(n_features):
            for j in range(n_samples):
                value = feature_contributions[i, j]
                if value > 0.5:  # 只标注较大的值
                    text_color = "white" if value > 1.5 else "black"
                    ax2.text(
                        j,
                        i,
                        f"{value:.1f}",
                        ha="center",
                        va="center",
                        color=text_color,
                        fontsize=7,
                    )

        ax2.set_xlabel("样本索引", fontsize=10)
        ax2.set_ylabel("特征", fontsize=10)
        ax2.set_title("特征异常贡献热图", fontsize=12, fontweight="bold")

        plt.tight_layout()
        return save_and_log_figure(artifact_name, "ECOD分解图已上传到 MLflow")

    except Exception as e:
        logger.error(f"绘制ECOD分解图失败: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return ""
