from typing import Dict, Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from redis.exceptions import RedisError

from apps.opspilot.metis.llm.tools.common.credentials import execute_with_credentials
from apps.opspilot.metis.llm.tools.redis.connection import build_redis_normalized_from_runnable, get_redis_connection_from_item
from apps.opspilot.metis.llm.tools.redis.utils import build_error_response, build_success_response


@tool()
def redis_zadd(
    key: str, members: Dict[str, float], instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None
):
    """向 Redis sorted set 批量添加带分值的成员。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response({"added": client.zadd(key, members)}, key=key)
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_zrange(
    key: str,
    start: int = 0,
    end: int = -1,
    withscores: bool = False,
    instance_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    config: RunnableConfig = None,
):
    """读取 Redis sorted set 指定区间内的成员，可选返回分值。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response(client.zrange(key, start, end, withscores=withscores), key=key)
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_zrem(
    key: str, member: str, instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None
):
    """从 Redis sorted set 中移除成员。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response({"removed": client.zrem(key, member)}, key=key)
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_zscore(
    key: str, member: str, instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None
):
    """获取 Redis sorted set 成员的分值。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response({"key": key, "member": member, "score": client.zscore(key, member)})
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_zcard(key: str, instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None):
    """获取 Redis sorted set 的成员数量。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response({"key": key, "count": client.zcard(key)})
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_zrevrange(
    key: str,
    start: int = 0,
    end: int = -1,
    withscores: bool = False,
    instance_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    config: RunnableConfig = None,
):
    """按分值倒序读取 Redis sorted set 区间成员。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response(client.zrevrange(key, start, end, withscores=withscores), key=key)
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_zrangebyscore(
    key: str,
    min_score: float,
    max_score: float,
    withscores: bool = False,
    instance_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    config: RunnableConfig = None,
):
    """按分值范围读取 Redis sorted set 成员。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response(client.zrangebyscore(key, min_score, max_score, withscores=withscores), key=key)
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_zrank(
    key: str, member: str, instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None
):
    """获取成员在 Redis sorted set 中的排名。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response({"key": key, "member": member, "rank": client.zrank(key, member)})
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)
