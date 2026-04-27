import os


class VictoriaLogsConstants:
    """VictoriaLogs服务相关常量"""

    # VictoriaLogs服务信息
    HOST = os.getenv("VICTORIALOGS_HOST")
    USER = os.getenv("VICTORIALOGS_USER")
    PWD = os.getenv("VICTORIALOGS_PWD")

    # SSL验证配置，支持环境变量控制
    SSL_VERIFY = os.getenv("VICTORIALOGS_SSL_VERIFY", "false").lower() == "true"

    # SSE连接配置
    MAX_CONNECTION_TIME = int(os.getenv("SSE_MAX_CONNECTION_TIME", "1800"))  # 默认30分钟
    KEEPALIVE_INTERVAL = int(os.getenv("SSE_KEEPALIVE_INTERVAL", "45"))  # 默认45秒

    # 查询保护：避免单次日志检索返回过大结果集，拖慢 VMLogs 和 Web 响应。
    QUERY_LIMIT_MAX = int(os.getenv("VICTORIALOGS_QUERY_LIMIT_MAX", "1000"))
    FIELD_VALUES_LIMIT_MAX = int(os.getenv("VICTORIALOGS_FIELD_VALUES_LIMIT_MAX", "1000"))
    HITS_FIELDS_LIMIT_MAX = int(os.getenv("VICTORIALOGS_HITS_FIELDS_LIMIT_MAX", "100"))

    @staticmethod
    def normalize_bounded_int(value, field_name: str, default: int, max_value: int, clamp: bool = False) -> int:
        if value in (None, ""):
            return default
        try:
            normalized = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} 必须是整数") from exc
        if normalized < 1:
            raise ValueError(f"{field_name} 必须大于等于 1")
        if normalized > max_value:
            if clamp:
                return max_value
            raise ValueError(f"{field_name} 不能大于 {max_value}")
        return normalized

    @classmethod
    def normalize_query_limit(cls, value, default: int = 10, clamp: bool = False) -> int:
        return cls.normalize_bounded_int(value, "limit", default, cls.QUERY_LIMIT_MAX, clamp=clamp)

    @classmethod
    def normalize_field_values_limit(cls, value, default: int = 100, clamp: bool = False) -> int:
        return cls.normalize_bounded_int(value, "limit", default, cls.FIELD_VALUES_LIMIT_MAX, clamp=clamp)

    @classmethod
    def normalize_hits_fields_limit(cls, value, default: int = 5, clamp: bool = False) -> int:
        return cls.normalize_bounded_int(value, "fields_limit", default, cls.HITS_FIELDS_LIMIT_MAX, clamp=clamp)
