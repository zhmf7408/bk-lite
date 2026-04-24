"""Oracle运维工具模块

这个模块包含了所有Oracle相关的运维工具函数,按功能分类到不同的子模块中:
- resources: 基础资源查询工具(数据库/表空间/表/索引/用户等)
- dynamic_queries: 动态SQL查询工具(安全的动态查询生成和执行)
- diagnostics: 故障诊断工具(慢查询/锁/连接/Data Guard等)
- monitoring: 监控指标采集工具
- optimization: 优化建议工具(表空间/索引/碎片/配置)
- utils: 通用辅助函数
- connection: 多实例连接管理
"""

# 工具集构造参数元数据
CONSTRUCTOR_PARAMS = [
    {"name": "oracle_instances", "type": "string", "required": False, "description": "Oracle多实例JSON配置"},
    {"name": "oracle_default_instance_id", "type": "string", "required": False, "description": "默认Oracle实例ID"},
]

# 基础资源查询工具
from apps.opspilot.metis.llm.tools.oracle.resources import (  # noqa: E402
    get_current_database_info,
    get_database_config,
    get_table_structure,
    list_oracle_indexes,
    list_oracle_tables,
    list_oracle_tablespaces,
    list_oracle_users,
)

# 动态SQL查询工具
from apps.opspilot.metis.llm.tools.oracle.dynamic_queries import (  # noqa: E402
    execute_safe_select,
    explain_query_plan,
    search_tables_by_keyword,
)

# 故障诊断工具
from apps.opspilot.metis.llm.tools.oracle.diagnostics import (  # noqa: E402
    check_database_health,
    check_dataguard_status,
    diagnose_connection_issues,
    diagnose_lock_conflicts,
    diagnose_slow_queries,
)

# 监控指标采集工具
from apps.opspilot.metis.llm.tools.oracle.monitoring import (  # noqa: E402
    check_redo_log_status,
    get_database_metrics,
    get_io_stats,
    get_processlist,
    get_sga_pga_stats,
    get_table_metrics,
)

# 优化建议工具
from apps.opspilot.metis.llm.tools.oracle.optimization import (  # noqa: E402
    check_configuration_tuning,
    check_table_fragmentation,
    check_tablespace_usage,
    check_unused_indexes,
)

# 通用工具函数
from apps.opspilot.metis.llm.tools.oracle.utils import (  # noqa: E402
    calculate_percentage,
    format_duration,
    format_size,
    prepare_context,
    safe_json_dumps,
)

__all__ = [
    # 构造参数
    "CONSTRUCTOR_PARAMS",
    # 基础资源查询工具
    "get_current_database_info",
    "list_oracle_tablespaces",
    "list_oracle_tables",
    "list_oracle_indexes",
    "get_table_structure",
    "list_oracle_users",
    "get_database_config",
    # 动态SQL查询工具
    "search_tables_by_keyword",
    "execute_safe_select",
    "explain_query_plan",
    # 故障诊断工具
    "diagnose_slow_queries",
    "diagnose_lock_conflicts",
    "diagnose_connection_issues",
    "check_database_health",
    "check_dataguard_status",
    # 监控指标采集工具
    "get_database_metrics",
    "get_table_metrics",
    "get_sga_pga_stats",
    "get_io_stats",
    "check_redo_log_status",
    "get_processlist",
    # 优化建议工具
    "check_tablespace_usage",
    "check_unused_indexes",
    "check_table_fragmentation",
    "check_configuration_tuning",
    # 通用工具函数
    "prepare_context",
    "format_size",
    "format_duration",
    "safe_json_dumps",
    "calculate_percentage",
]
