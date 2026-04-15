import json
from typing import Any, Dict, Literal, Optional
from urllib.parse import urlparse

import redis
from langchain_core.runnables import RunnableConfig
from redis import Redis
from redis.cluster import RedisCluster

REDIS_INSTANCE_FIELDS = (
    "id",
    "name",
    "url",
    "username",
    "password",
    "ssl",
    "ssl_ca_path",
    "ssl_keyfile",
    "ssl_certfile",
    "ssl_cert_reqs",
    "ssl_ca_certs",
    "cluster_mode",
)


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def parse_redis_url(url: str) -> Dict[str, Any]:
    parsed = urlparse(url)
    db = 0
    if parsed.path and parsed.path != "/":
        try:
            db = int(parsed.path.strip("/"))
        except ValueError:
            db = 0
    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 6379,
        "db": db,
        "username": parsed.username,
        "password": parsed.password,
        "ssl": parsed.scheme == "rediss",
    }


def normalize_redis_instance(instance: Dict[str, Any], fallback_name: str = "Redis - 1", fallback_id: str = "redis-1") -> Dict[str, Any]:
    normalized = {key: instance.get(key) for key in REDIS_INSTANCE_FIELDS}
    normalized["id"] = _normalize_text(normalized.get("id")) or fallback_id
    normalized["name"] = _normalize_text(normalized.get("name")) or fallback_name
    normalized["url"] = _normalize_text(normalized.get("url"))
    normalized["username"] = _normalize_text(normalized.get("username"))
    normalized["password"] = _normalize_text(normalized.get("password"))
    normalized["ssl"] = _normalize_bool(normalized.get("ssl"))
    normalized["ssl_ca_path"] = _normalize_text(normalized.get("ssl_ca_path"))
    normalized["ssl_keyfile"] = _normalize_text(normalized.get("ssl_keyfile"))
    normalized["ssl_certfile"] = _normalize_text(normalized.get("ssl_certfile"))
    normalized["ssl_cert_reqs"] = _normalize_text(normalized.get("ssl_cert_reqs"))
    normalized["ssl_ca_certs"] = _normalize_text(normalized.get("ssl_ca_certs"))
    normalized["cluster_mode"] = _normalize_bool(normalized.get("cluster_mode"))
    return normalized


def parse_redis_instances(raw_instances: Any) -> list[Dict[str, Any]]:
    if not raw_instances:
        return []

    parsed_instances = raw_instances
    if isinstance(raw_instances, str):
        try:
            parsed_instances = json.loads(raw_instances)
        except json.JSONDecodeError:
            return []

    if not isinstance(parsed_instances, list):
        return []

    normalized_instances = []
    for index, instance in enumerate(parsed_instances, start=1):
        if not isinstance(instance, dict):
            continue
        normalized_instances.append(
            normalize_redis_instance(instance, fallback_name=f"Redis - {index}", fallback_id=f"redis-{index}")
        )
    return normalized_instances


def get_redis_instances_from_configurable(configurable: Dict[str, Any]) -> tuple[list[Dict[str, Any]], str]:
    instances = parse_redis_instances(configurable.get("redis_instances"))
    default_instance_id = _normalize_text(configurable.get("redis_default_instance_id"))
    return instances, default_instance_id


def _build_legacy_redis_config(configurable: Dict[str, Any]) -> Dict[str, Any]:
    redis_url = configurable.get("url") or configurable.get("redis_url")
    if redis_url:
        parsed = parse_redis_url(redis_url)
        if configurable.get("username"):
            parsed["username"] = configurable.get("username")
        if configurable.get("password"):
            parsed["password"] = configurable.get("password")
        if configurable.get("ssl") is not None:
            parsed["ssl"] = _normalize_bool(configurable.get("ssl"))
        parsed["ssl_ca_path"] = configurable.get("ssl_ca_path")
        parsed["ssl_keyfile"] = configurable.get("ssl_keyfile")
        parsed["ssl_certfile"] = configurable.get("ssl_certfile")
        parsed["ssl_cert_reqs"] = configurable.get("ssl_cert_reqs")
        parsed["ssl_ca_certs"] = configurable.get("ssl_ca_certs")
        parsed["cluster_mode"] = _normalize_bool(configurable.get("cluster_mode", False))
        return parsed
    return {
        "host": configurable.get("host", "127.0.0.1"),
        "port": configurable.get("port", 6379),
        "db": configurable.get("db", 0),
        "username": configurable.get("username"),
        "password": configurable.get("password"),
        "ssl": _normalize_bool(configurable.get("ssl", False)),
        "ssl_ca_path": configurable.get("ssl_ca_path"),
        "ssl_keyfile": configurable.get("ssl_keyfile"),
        "ssl_certfile": configurable.get("ssl_certfile"),
        "ssl_cert_reqs": configurable.get("ssl_cert_reqs"),
        "ssl_ca_certs": configurable.get("ssl_ca_certs"),
        "cluster_mode": _normalize_bool(configurable.get("cluster_mode", False)),
    }


def build_redis_config_from_instance(instance: Dict[str, Any]) -> Dict[str, Any]:
    normalized = normalize_redis_instance(instance)
    params: Dict[str, Any]
    if normalized.get("url"):
        params = parse_redis_url(normalized["url"])
    else:
        params = {"host": "127.0.0.1", "port": 6379, "db": 0, "username": None, "password": None, "ssl": False}
    if normalized.get("username"):
        params["username"] = normalized.get("username")
    if normalized.get("password"):
        params["password"] = normalized.get("password")
    if normalized.get("ssl") is not None:
        params["ssl"] = normalized.get("ssl")
    params["ssl_ca_path"] = normalized.get("ssl_ca_path") or None
    params["ssl_keyfile"] = normalized.get("ssl_keyfile") or None
    params["ssl_certfile"] = normalized.get("ssl_certfile") or None
    params["ssl_cert_reqs"] = normalized.get("ssl_cert_reqs") or None
    params["ssl_ca_certs"] = normalized.get("ssl_ca_certs") or None
    params["cluster_mode"] = normalized.get("cluster_mode", False)
    return params


def get_redis_instances_prompt(configurable: Dict[str, Any]) -> str:
    instances, default_instance_id = get_redis_instances_from_configurable(configurable)
    if not instances:
        return ""

    default_instance = resolve_redis_instance(instances, default_instance_id)
    available_instances = ", ".join(instance["name"] for instance in instances if instance.get("name"))
    return (
        "已配置多个 Redis 实例。"
        f"默认实例: {default_instance['name']}。"
        f"可用实例: {available_instances}。"
        "如需切换实例，请在工具调用时显式传入 instance_name 或 instance_id。"
    )


def resolve_redis_instance(
    instances: list[Dict[str, Any]],
    default_instance_id: str = "",
    instance_name: Optional[str] = None,
    instance_id: Optional[str] = None,
) -> Dict[str, Any]:
    if not instances:
        raise ValueError("No Redis instances configured")

    if instance_id:
        for instance in instances:
            if instance.get("id") == instance_id:
                return instance
        raise ValueError(f"Redis instance not found: {instance_id}")

    if instance_name:
        for instance in instances:
            if instance.get("name") == instance_name:
                return instance
        raise ValueError(f"Redis instance not found: {instance_name}")

    if default_instance_id:
        for instance in instances:
            if instance.get("id") == default_instance_id:
                return instance

    return instances[0]


def build_redis_config_from_runnable(
    config: Optional[RunnableConfig], instance_name: Optional[str] = None, instance_id: Optional[str] = None
) -> Dict[str, Any]:
    configurable = config.get("configurable", {}) if config else {}
    instances, default_instance_id = get_redis_instances_from_configurable(configurable)

    if instances:
        instance = resolve_redis_instance(instances, default_instance_id, instance_name=instance_name, instance_id=instance_id)
        return build_redis_config_from_instance(instance)

    if instance_name or instance_id:
        raise ValueError("Redis instance selection is unavailable for legacy single-instance configuration")

    return _build_legacy_redis_config(configurable)


def _create_redis_client(params: Dict[str, Any], decode_responses: bool = True):
    cluster_mode = params.pop("cluster_mode", False)
    params["decode_responses"] = decode_responses
    if cluster_mode:
        params.pop("db", None)
        return RedisCluster(**{k: v for k, v in params.items() if v is not None})
    return redis.Redis(**{k: v for k, v in params.items() if v is not None})


def get_redis_connection(
    config: Optional[RunnableConfig] = None,
    decode_responses: bool = True,
    instance_name: Optional[str] = None,
    instance_id: Optional[str] = None,
):
    params = build_redis_config_from_runnable(config, instance_name=instance_name, instance_id=instance_id)
    return _create_redis_client(params, decode_responses=decode_responses)


def get_binary_redis_connection(
    config: Optional[RunnableConfig] = None, instance_name: Optional[str] = None, instance_id: Optional[str] = None
):
    return get_redis_connection(
        config=config, decode_responses=False, instance_name=instance_name, instance_id=instance_id
    )


def test_redis_instance(instance: Dict[str, Any]) -> bool:
    normalized = normalize_redis_instance(instance)
    if not normalized.get("url"):
        raise ValueError("Redis URL is required")
    client = _create_redis_client(build_redis_config_from_instance(normalized), decode_responses=True)
    try:
        return bool(client.ping())
    finally:
        if isinstance(client, Redis):
            client.close()


from apps.opspilot.metis.llm.tools.common.credentials import (
    CredentialAdapter,
    CredentialItem,
    CredentialValidationError,
    NormalizedCredentials,
    execute_with_credentials,
    normalize_credentials,
)

REDIS_FLAT_FIELDS = ["url", "redis_url", "host", "username", "password", "ssl", "ssl_ca_path", "ssl_keyfile", "ssl_certfile", "ssl_cert_reqs", "ssl_ca_certs", "cluster_mode"]


class RedisCredentialAdapter:
    flat_fields = REDIS_FLAT_FIELDS

    def build_from_flat_config(self, configurable: Dict[str, Any]) -> Dict[str, Any]:
        return _build_legacy_redis_config(configurable)

    def build_from_credential_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return build_redis_config_from_instance(item)

    def validate(self, config: Dict[str, Any]) -> None:
        if not config.get("host") and not config.get("url"):
            raise CredentialValidationError("Redis host/url is required")

    def get_display_name(self, source: Dict[str, Any], index: int) -> str:
        return source.get("name") or f"Redis - {index + 1}"


_redis_adapter = RedisCredentialAdapter()


def build_redis_normalized_from_runnable(
    config: Optional[RunnableConfig],
    instance_name: Optional[str] = None,
    instance_id: Optional[str] = None,
) -> NormalizedCredentials:
    """
    Build NormalizedCredentials from RunnableConfig.

    - If redis_instances is configured with a specific instance_name/id: single-mode targeting that instance.
    - If redis_instances is configured without instance selection: multi-mode (all instances) when count > 1, single-mode when count == 1.
    - If no redis_instances: legacy single-mode from flat fields.
    """
    configurable = config.get("configurable", {}) if config else {}
    instances, default_instance_id = get_redis_instances_from_configurable(configurable)

    if instances:
        if instance_name or instance_id:
            instance = resolve_redis_instance(instances, default_instance_id, instance_name=instance_name, instance_id=instance_id)
            redis_config = build_redis_config_from_instance(instance)
            return NormalizedCredentials(
                mode="single",
                legacy_single=False,
                items=[CredentialItem(index=0, name=instance.get("name", "Redis - 1"), raw=instance, config=redis_config)],
            )

        mode: Literal["single", "multi"] = "single" if len(instances) == 1 else "multi"
        items = []
        for i, instance in enumerate(instances):
            redis_config = build_redis_config_from_instance(instance)
            items.append(CredentialItem(index=i, name=instance.get("name", f"Redis - {i + 1}"), raw=instance, config=redis_config))
        return NormalizedCredentials(mode=mode, legacy_single=False, items=items)

    # Legacy mode or credentials-list mode
    return normalize_credentials(configurable, _redis_adapter)


def get_redis_connection_from_item(item: CredentialItem, decode_responses: bool = True):
    """Create a Redis client from a CredentialItem (for use in executors)."""
    return _create_redis_client(item["config"].copy(), decode_responses=decode_responses)


def get_binary_redis_connection_from_item(item: CredentialItem):
    return get_redis_connection_from_item(item, decode_responses=False)
