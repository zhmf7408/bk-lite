## 1. 项目结构与依赖

- [x] 1.1 在 `server/pyproject.toml` 中新增 `mysql-connector-python` 依赖
- [x] 1.2 创建 `server/apps/opspilot/metis/llm/tools/mysql/` 目录及 `__init__.py`，定义 `CONSTRUCTOR_PARAMS`（`mysql_instances`、`mysql_default_instance_id`）

## 2. 连接管理（connection.py）

- [x] 2.1 定义 `MYSQL_INSTANCE_FIELDS` 元组（id/name/host/port/database/user/password/charset/collation/ssl/ssl_ca/ssl_cert/ssl_key）
- [x] 2.2 实现 `parse_mysql_instances()`：解析 JSON 字符串为实例列表，含字段归一化和默认值（port=3306, database=mysql, charset=utf8mb4, collation=utf8mb4_unicode_ci）
- [x] 2.3 实现 `resolve_mysql_instance()`：按 instance_id/instance_name/default_instance_id 定位实例
- [x] 2.4 实现 `MysqlCredentialAdapter`（实现 `CredentialAdapter` 协议的 4 个方法）
- [x] 2.5 实现 `build_mysql_normalized_from_runnable()`：多实例 → NormalizedCredentials，含 legacy 平铺字段回退
- [x] 2.6 实现 `get_mysql_connection_from_item()`：从 CredentialItem 创建 mysql.connector 连接（含 charset/collation/autocommit/sql_mode 配置）
- [x] 2.7 实现 `get_mysql_instances_prompt()`：生成多实例上下文提示文本

## 3. 公共工具函数（utils.py）

- [x] 3.1 实现 `prepare_context()`：从 RunnableConfig 提取 configurable
- [x] 3.2 实现 `execute_readonly_query()`：`SET SESSION TRANSACTION READ ONLY` + 执行查询 + 返回结果
- [x] 3.3 实现 `validate_sql_safety()`：通用禁止词 + MySQL 特有禁止词（LOAD/HANDLER/FLUSH/PURGE/RESET/CHANGE/INSTALL/UNINSTALL/PREPARE/EXECUTE/DEALLOCATE/KILL/LOCK/UNLOCK）
- [x] 3.4 实现 `format_size()`、`format_duration()`、`parse_mysql_version()`、`safe_json_dumps()`、`calculate_percentage()`

## 4. 资源发现工具（resources.py）— 8 个工具

- [x] 4.1 实现 `get_current_database_info`：返回版本、字符集、引擎、运行时间等
- [x] 4.2 实现 `list_mysql_databases`：列出所有数据库及大小
- [x] 4.3 实现 `list_mysql_tables`：列出指定数据库的所有表
- [x] 4.4 实现 `list_mysql_indexes`：列出表的索引信息
- [x] 4.5 实现 `list_mysql_schemas`：列出 schema
- [x] 4.6 实现 `get_table_structure`：返回列定义、类型、约束、索引、注释
- [x] 4.7 实现 `list_mysql_users`：列出用户及权限概览
- [x] 4.8 实现 `get_database_config`：返回关键配置变量

## 5. 动态查询工具（dynamic.py）— 5 个工具

- [x] 5.1 实现 `get_table_schema_details`：获取表详细 schema（含注释、外键）
- [x] 5.2 实现 `search_tables_by_keyword`：按关键词搜索表名/列名
- [x] 5.3 实现 `execute_safe_select`：安全执行 SELECT（validate_sql_safety + 只读事务 + 敏感字段屏蔽）
- [x] 5.4 实现 `explain_query_plan`：执行 EXPLAIN 返回执行计划
- [x] 5.5 实现 `get_sample_data`：获取表样本数据（屏蔽敏感字段，禁止 SELECT *）

## 6. 故障诊断工具（diagnostics.py）— 7 个工具

- [x] 6.1 实现 `diagnose_slow_queries`：从 performance_schema 获取慢查询
- [x] 6.2 实现 `diagnose_lock_conflicts`：查询 InnoDB 锁等待信息
- [x] 6.3 实现 `diagnose_connection_issues`：连接数分析（当前/最大/异常）
- [x] 6.4 实现 `check_database_health`：综合健康检查
- [x] 6.5 实现 `check_replication_lag`：主从复制延迟检查
- [x] 6.6 实现 `diagnose_deadlocks`：解析 SHOW ENGINE INNODB STATUS 死锁信息
- [x] 6.7 实现 `get_failed_queries`：失败/错误查询统计

## 7. 运行监控工具（monitoring.py）— 8 个工具

- [x] 7.1 实现 `get_database_metrics`：QPS、TPS、连接数等核心指标
- [x] 7.2 实现 `get_table_metrics`：表行数、大小、碎片率
- [x] 7.3 实现 `get_innodb_stats`：缓冲池、脏页、IO、行锁等 InnoDB 指标
- [x] 7.4 实现 `get_io_stats`：磁盘 IO 统计（performance_schema）
- [x] 7.5 实现 `check_binary_log_status`：Binlog 状态与空间占用
- [x] 7.6 实现 `check_replication_status`：主从复制详细状态
- [x] 7.7 实现 `get_processlist`：当前活跃会话列表
- [x] 7.8 实现 `check_database_size_growth`：数据库空间增长趋势

## 8. 优化建议工具（optimization.py）— 4 个工具

- [x] 8.1 实现 `check_unused_indexes`：检测未使用的索引
- [x] 8.2 实现 `recommend_index_optimization`：冗余索引、缺失索引建议
- [x] 8.3 实现 `check_table_fragmentation`：表碎片分析与 OPTIMIZE 建议
- [x] 8.4 实现 `check_configuration_tuning`：配置调优建议

## 9. 性能分析工具（analysis.py）— 3 个工具

- [x] 9.1 实现 `analyze_buffer_pool_usage`：缓冲池命中率、淘汰率、页分布
- [x] 9.2 实现 `analyze_query_patterns`：基于 events_statements_summary_by_digest 的查询模式分析
- [x] 9.3 实现 `analyze_table_statistics`：表访问模式统计（读写比、全表扫描次数）

## 10. 工具注册与集成

- [x] 10.1 在 `tools_loader.py` 中添加 `from apps.opspilot.metis.llm.tools import mysql` 和 `"mysql": (mysql, False)` 注册
- [x] 10.2 在 `__init__.py` 中完成所有 35 个工具的导入和 `__all__` 导出

## 11. 验证

- [x] 11.1 验证 `tools_loader` 能正确加载 mysql 模块并发现 35 个 StructuredTool
- [x] 11.2 验证多实例配置下批量执行返回聚合结果格式正确
- [x] 11.3 验证单实例指定下返回非包装结果
- [x] 11.4 验证 legacy 平铺字段配置兼容性
- [x] 11.5 验证 `validate_sql_safety()` 拦截所有 MySQL 特有危险关键词
- [x] 11.6 执行 `cd server && make test` 确保无回归
