# -- coding: utf-8 --
# @File: plugin_handler.py
# @Time: 2025/12/19
# @Author: AI Assistant
"""
插件采集任务处理器
处理各种插件（MySQL、Redis、Nginx等）的数据采集任务
"""

import time
import traceback
import ntpath
import posixpath
from typing import Dict, Any
from sanic.log import logger


def _is_config_file_callback(params: Dict[str, Any]) -> bool:
    return (
        str(params.get("callback_subject") or "") == "receive_config_file_result"
        or str(params.get("plugin_name") or "") == "config_file_info"
        or str(params.get("model_id") or "") == "config_file"
    )


def _resolve_callback_identity(params: Dict[str, Any]) -> Dict[str, str]:
    host = str(params.get("host") or params.get("instance_name") or "")

    return {
        "instance_id": host,
        "instance_name": host,
        "model_id": str(
            params.get("target_model_id")
            or params.get("model_id")
            or "host"
        ),
    }


def _extract_file_name(file_path: str) -> str:
    normalized_path = str(file_path or "").strip()
    if not normalized_path:
        return ""
    if ":\\" in normalized_path or "\\" in normalized_path:
        return ntpath.basename(normalized_path)
    return posixpath.basename(normalized_path)


async def collect_plugin_task(
    ctx: Dict, params: Dict[str, Any], task_id: str
) -> Dict[str, Any]:
    """
    插件采集任务处理器

    Args:
        ctx: ARQ 上下文
        params: 采集参数，包含 plugin_name 等
        task_id: 任务ID

    Returns:
        任务执行结果
    """
    plugin_name = params.get("plugin_name")
    logger.info(f"[Plugin Task] Processing: {task_id}, plugin: {plugin_name}")

    try:
        # 导入服务和工具（延迟导入避免循环依赖）
        from service.collection_service import CollectionService
        from tasks.utils.nats_helper import publish_metrics_to_nats
        from tasks.utils.nats_helper import publish_callback_to_nats
        from tasks.utils.metrics_helper import generate_plugin_error_metrics

        # 执行采集
        collect_service = CollectionService(params)
        metrics_data = await collect_service.collect()

        logger.info(f"[Plugin Task] {task_id} completed successfully")

        if params.get("callback_subject"):
            await publish_callback_to_nats(metrics_data, params, task_id)
        else:
            await publish_metrics_to_nats(ctx, metrics_data, params, task_id)

        return {
            "task_id": task_id,
            "status": "success",
            "plugin_name": plugin_name,
            "completed_at": int(time.time() * 1000),
        }

    except Exception as e:
        logger.error(
            f"[Plugin Task] {task_id} failed: {str(e)}\n{traceback.format_exc()}"
        )

        # 导入工具函数
        from tasks.utils.nats_helper import publish_metrics_to_nats
        from tasks.utils.nats_helper import publish_callback_to_nats
        from tasks.utils.metrics_helper import generate_plugin_error_metrics

        if params.get("callback_subject"):
            identity = _resolve_callback_identity(params) if _is_config_file_callback(params) else {
                "instance_id": str(params.get("instance_id") or params.get("host") or ""),
                "model_id": str(params.get("target_model_id") or params.get("model_id") or "host"),
            }
            await publish_callback_to_nats(
                {
                    "collect_task_id": params.get("collect_task_id"),
                    "instance_id": identity["instance_id"],
                    "instance_name": identity["instance_name"],
                    "model_id": identity["model_id"],
                    "file_path": params.get("config_file_path", ""),
                    "file_name": _extract_file_name(params.get("config_file_path", "")),
                    "version": str(int(time.time())),
                    "status": "error",
                    "size": 0,
                    "error": str(e),
                    "content_base64": "",
                },
                params,
                task_id,
            )
        else:
            error_metrics = generate_plugin_error_metrics(params, e)
            await publish_metrics_to_nats(ctx, error_metrics, params, task_id)

        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
            "plugin_name": plugin_name,
            "completed_at": int(time.time() * 1000),
        }
