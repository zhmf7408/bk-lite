import json
from typing import Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from redis.exceptions import RedisError

from apps.opspilot.metis.llm.tools.common.credentials import execute_with_credentials
from apps.opspilot.metis.llm.tools.redis.connection import build_redis_normalized_from_runnable, get_redis_connection_from_item
from apps.opspilot.metis.llm.tools.redis.utils import build_error_response, build_success_response


@tool()
def redis_json_set(
    name: str,
    path: str,
    value: str,
    expire_seconds: Optional[int] = None,
    instance_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    config: RunnableConfig = None,
):
    """在 Redis JSON 文档指定 path 写入值。"""
    try:
        parsed_value = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        parsed_value = value
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            client.json().set(name, path, parsed_value)
            if expire_seconds is not None:
                client.expire(name, expire_seconds)
            return build_success_response({"name": name, "path": path, "expire_seconds": expire_seconds})
        except (RedisError, ValueError) as e:
            return build_error_response(e, error_type="unsupported_feature")

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_json_get(
    name: str, path: str = "$", instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None
):
    """读取 Redis JSON 文档指定 path 的值。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response(client.json().get(name, path))
        except (RedisError, ValueError) as e:
            return build_error_response(e, error_type="unsupported_feature")

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_json_del(
    name: str, path: str = "$", instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None
):
    """删除 Redis JSON 文档指定 path 的值。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response({"name": name, "path": path, "deleted": client.json().delete(name, path)})
        except (RedisError, ValueError) as e:
            return build_error_response(e, error_type="unsupported_feature")

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_json_arrappend(
    name: str,
    path: str,
    values: list,
    instance_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    config: RunnableConfig = None,
):
    """向 Redis JSON 数组 path 追加元素。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response(client.json().arrappend(name, path, *values))
        except (RedisError, ValueError) as e:
            return build_error_response(e, error_type="unsupported_feature")

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_json_objkeys(
    name: str, path: str = "$", instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None
):
    """获取 Redis JSON 对象的 key 列表。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response(client.json().objkeys(name, path))
        except (RedisError, ValueError) as e:
            return build_error_response(e, error_type="unsupported_feature")

    return execute_with_credentials(normalized, _executor)
