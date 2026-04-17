from typing import Any, Dict, Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from redis.exceptions import RedisError

from apps.opspilot.metis.llm.tools.common.credentials import execute_with_credentials
from apps.opspilot.metis.llm.tools.redis.connection import build_redis_normalized_from_runnable, get_redis_connection_from_item
from apps.opspilot.metis.llm.tools.redis.utils import build_error_response, build_success_response


@tool()
def redis_xadd(
    key: str,
    fields: Dict[str, Any],
    expiration: Optional[int] = None,
    instance_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    config: RunnableConfig = None,
):
    """向 Redis stream 追加消息。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            entry_id = client.xadd(key, fields)
            if expiration is not None:
                client.expire(key, expiration)
            return build_success_response({"key": key, "entry_id": entry_id, "expiration": expiration})
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_xread(
    streams: Dict[str, str],
    count: Optional[int] = None,
    block: Optional[int] = None,
    instance_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    config: RunnableConfig = None,
):
    """从一个或多个 Redis stream 读取消息。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response(client.xread(streams=streams, count=count, block=block))
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_xrange(
    key: str,
    min_id: str = "-",
    max_id: str = "+",
    count: Optional[int] = None,
    instance_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    config: RunnableConfig = None,
):
    """正序读取 Redis stream 范围消息。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response(client.xrange(key, min=min_id, max=max_id, count=count), key=key)
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_xrevrange(
    key: str,
    max_id: str = "+",
    min_id: str = "-",
    count: Optional[int] = None,
    instance_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    config: RunnableConfig = None,
):
    """倒序读取 Redis stream 范围消息。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response(client.xrevrange(key, max=max_id, min=min_id, count=count), key=key)
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_xdel(
    key: str, entry_id: str, instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None
):
    """删除 Redis stream 指定消息。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response({"key": key, "deleted": client.xdel(key, entry_id), "entry_id": entry_id})
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_xgroup_create(
    key: str,
    group_name: str,
    id: str = "$",
    mkstream: bool = False,
    instance_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    config: RunnableConfig = None,
):
    """创建 Redis stream consumer group。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response(
                {"created": client.xgroup_create(key, group_name, id=id, mkstream=mkstream), "key": key, "group_name": group_name}
            )
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_xreadgroup(
    group_name: str,
    consumer_name: str,
    streams: Dict[str, str],
    count: Optional[int] = None,
    block: Optional[int] = None,
    instance_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    config: RunnableConfig = None,
):
    """以 consumer group 方式读取 Redis stream。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response(client.xreadgroup(group_name, consumer_name, streams=streams, count=count, block=block))
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_xack(
    key: str,
    group_name: str,
    entry_ids: list[str],
    instance_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    config: RunnableConfig = None,
):
    """确认 Redis stream consumer group 消息。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response({"acked": client.xack(key, group_name, *entry_ids), "key": key, "group_name": group_name})
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)
