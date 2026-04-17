"""绘图通用工具 - 图片保存、MLflow artifact 上传、临时文件清理."""

import os

import mlflow
import matplotlib.pyplot as plt
from loguru import logger


def save_and_log_figure(artifact_name: str, log_message: str) -> str:
    """保存当前 matplotlib figure 为 PNG，上传到 MLflow artifact 并清理临时文件.

    调用方应在调用本函数前完成所有绑定到当前 figure 的绑图操作（包括 tight_layout）。
    本函数会调用 ``plt.close()`` 关闭当前 figure。

    Args:
        artifact_name: 文件名（不含扩展名），生成 ``{artifact_name}.png``。
        log_message: 上传成功时的日志消息前缀。

    Returns:
        生成的图片文件路径（``{artifact_name}.png``）。
    """
    img_path = f"{artifact_name}.png"
    plt.savefig(img_path, dpi=150, bbox_inches="tight")

    if mlflow.active_run():
        mlflow.log_artifact(img_path)
        logger.info(f"{log_message}: {img_path}")

        try:
            os.remove(img_path)
            logger.debug(f"本地临时文件已删除: {img_path}")
        except Exception as e:
            logger.warning(f"删除临时文件失败: {img_path}, 错误: {e}")

    plt.close()
    return img_path
