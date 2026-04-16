from typing import Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from redis.exceptions import RedisError

from apps.opspilot.metis.llm.tools.common.credentials import execute_with_credentials
from apps.opspilot.metis.llm.tools.redis.connection import build_redis_normalized_from_runnable, get_redis_connection_from_item
from apps.opspilot.metis.llm.tools.redis.utils import build_error_response, build_success_response


@tool()
def redis_publish(
    channel: str, message: str, instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None
):
    """向 Redis channel 发布消息。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response({"channel": channel, "receivers": client.publish(channel, message)})
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_pubsub_channels(
    pattern: str = "*", instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None
):
    """列出当前 Redis pubsub channels。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            return build_success_response(client.pubsub_channels(pattern))
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_subscribe(
    channel: str, instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None
):
    """短调用方式订阅 Redis channel。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            pubsub = client.pubsub()
            pubsub.subscribe(channel)
            return build_success_response({"channel": channel, "subscribed": True})
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)


@tool()
def redis_unsubscribe(
    channel: str, instance_name: Optional[str] = None, instance_id: Optional[str] = None, config: RunnableConfig = None
):
    """短调用方式取消订阅 Redis channel。"""
    normalized = build_redis_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        try:
            client = get_redis_connection_from_item(item)
            pubsub = client.pubsub()
            pubsub.unsubscribe(channel)
            return build_success_response({"channel": channel, "unsubscribed": True})
        except (RedisError, ValueError) as e:
            return build_error_response(e)

    return execute_with_credentials(normalized, _executor)
