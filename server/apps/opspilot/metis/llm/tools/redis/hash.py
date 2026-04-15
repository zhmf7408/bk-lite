from typing import List, Optional

import numpy as np
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from redis.exceptions import RedisError

from apps.opspilot.metis.llm.tools.common.credentials import execute_with_credentials
from apps.opspilot.metis.llm.tools.redis.connection import (
    build_redis_normalized_from_runnable,
    get_binary_redis_connection_from_item,
    get_redis_connection_from_item,
)
from apps.opspilot.metis.llm.tools.redis.utils import build_error_response, build_success_response


@tool()
def redis_hset(
    name: str,
    key: str,
    value: str | int | float,
    expire_seconds: Optional[int] = None,
    instance_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    config: RunnableConfig = None,
):
    """设置 Redis hash 中的字段值，可选过期时间。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            client.hset(name, key, value)
            if expire_seconds is not None:
                client.expire(name, expire_seconds)
            return build_success_response({"name": name, "key": key, "expire_seconds": expire_seconds})
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_hgetall(name: str, instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None):
    """读取 Redis hash 的全部字段和值。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response(client.hgetall(name), name=name)
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_hget(
    name: str, key: str, instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None
):
    """读取 Redis hash 指定字段的值。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response({"name": name, "key": key, "value": client.hget(name, key)})
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_hdel(
    name: str, key: str, instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None
):
    """删除 Redis hash 指定字段。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response({"name": name, "key": key, "deleted": client.hdel(name, key)})
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_hexists(
    name: str, key: str, instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None
):
    """检查 Redis hash 中字段是否存在。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response({"name": name, "key": key, "exists": bool(client.hexists(name, key))})
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_hkeys(name: str, instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None):
    """获取 Redis hash 的全部字段名。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response(client.hkeys(name))
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_hvals(name: str, instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None):
    """获取 Redis hash 的全部字段值。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response(client.hvals(name))
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_hlen(name: str, instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None):
    """获取 Redis hash 的字段数量。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response({"name": name, "length": client.hlen(name)})
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_set_vector_in_hash(
    name: str,
    vector: List[float],
    vector_field: str = "vector",
    instance_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    config: RunnableConfig = None,
):
    """将向量以 float32 二进制形式写入 Redis hash。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            vector_blob = np.array(vector, dtype=np.float32).tobytes()
            client.hset(name, vector_field, vector_blob)
            return build_success_response({"name": name, "vector_field": vector_field, "stored": True})
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_get_vector_from_hash(
    name: str,
    vector_field: str = "vector",
    instance_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    config: RunnableConfig = None,
):
    """从 Redis hash 读取 float32 二进制向量并还原。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_binary_redis_connection_from_item(item)
            binary_blob = client.hget(name, vector_field)
            if not binary_blob:
                return build_success_response([])
            vector_array = np.frombuffer(binary_blob, dtype=np.float32)
            return build_success_response(vector_array.tolist())
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)
