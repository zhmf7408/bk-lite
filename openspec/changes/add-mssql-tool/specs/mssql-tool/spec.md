## ADDED Requirements

### Requirement: MSSQL 工具模块结构

系统 SHALL 在 `server/apps/opspilot/metis/llm/tools/mssql/` 目录下提供 MSSQL 工具模块，包含以下子模块：
- `__init__.py`: 工具集入口，定义 CONSTRUCTOR_PARAMS 和导出所有工具函数
- `utils.py`: 连接管理和通用工具函数
- `resources.py`: 基础资源查询工具
- `dynamic.py`: 动态 SQL 安全查询工具
- `diagnostics.py`: 故障诊断工具
- `monitoring.py`: 监控指标采集工具

#### Scenario: 模块加载成功
- **WHEN** 系统启动并加载 MSSQL 工具模块
- **THEN** `tools_loader.py` 的 `TOOL_MODULES` 字典中包含 `mssql` 键，且工具函数被正确注册

#### Scenario: CONSTRUCTOR_PARAMS 定义正确
- **WHEN** 获取 MSSQL 工具的构造参数元数据
- **THEN** 返回包含 host、port、database、user、password 的参数列表，与 PostgreSQL 工具格式一致

---

### Requirement: MSSQL 连接管理

系统 SHALL 通过 `utils.py` 提供 MSSQL 数据库连接管理功能，使用 pyodbc 驱动。

连接参数：
- host: MSSQL 服务器地址，默认 localhost
- port: 端口，默认 1433
- database: 默认连接的数据库
- user: 用户名
- password: 密码

#### Scenario: 成功建立数据库连接
- **WHEN** 调用 `get_db_connection` 函数并提供有效的连接参数
- **THEN** 返回 pyodbc 连接对象，连接超时设置为 10 秒

#### Scenario: 连接失败返回清晰错误
- **WHEN** 连接参数无效或服务器不可达
- **THEN** 抛出异常并记录错误日志，包含服务器地址和端口信息

#### Scenario: 使用 RunnableConfig 传递参数
- **WHEN** 工具函数通过 `config: RunnableConfig` 参数接收配置
- **THEN** `prepare_context` 函数从 `config.configurable` 中提取连接参数

---

### Requirement: 基础资源查询工具

系统 SHALL 在 `resources.py` 中提供以下基础资源查询工具，每个工具使用 `@tool` 装饰器：

| 工具函数 | 功能描述 |
|----------|----------|
| `list_mssql_databases` | 列出所有数据库及基本信息（大小、状态、兼容级别） |
| `list_mssql_tables` | 列出指定数据库的表（表名、行数估算、大小） |
| `list_mssql_indexes` | 列出表的索引信息（索引名、类型、列） |
| `list_mssql_schemas` | 列出数据库中的 Schema |
| `get_table_structure` | 获取表结构详情（列名、类型、约束） |
| `get_current_database_info` | 获取当前连接的数据库信息 |
| `list_mssql_logins` | 列出数据库登录名和角色 |

#### Scenario: 列出所有数据库
- **WHEN** 调用 `list_mssql_databases` 工具
- **THEN** 返回 JSON 格式结果，包含 `total_databases` 和 `databases` 数组，每个数据库包含 name、size、state、compatibility_level

#### Scenario: 查询指定数据库的表
- **WHEN** 调用 `list_mssql_tables(database="mydb", schema_name="dbo")` 
- **THEN** 返回该数据库中 dbo schema 下所有表的列表，包含表名、行数估算、数据大小

#### Scenario: 获取表结构
- **WHEN** 调用 `get_table_structure(table="users", schema_name="dbo")`
- **THEN** 返回表的列定义、主键、外键、索引信息的 JSON 结构

---

### Requirement: 动态 SQL 安全查询工具

系统 SHALL 在 `dynamic.py` 中提供安全的动态 SQL 查询工具，实现与 PostgreSQL 相同的安全机制。

安全要求：
- 仅允许 SELECT 和 WITH 开头的查询
- 禁止 INSERT、UPDATE、DELETE、DROP、CREATE、ALTER 等写操作
- 禁止多语句执行（分号分隔）
- 禁止查询敏感字段（password、secret、token 等）
- 自动添加 LIMIT/TOP 限制

#### Scenario: 执行合法 SELECT 查询
- **WHEN** 调用 `execute_safe_select(sql="SELECT id, name FROM users WHERE status = 'active'", limit=100)`
- **THEN** 返回查询结果的 JSON 格式，包含 success、row_count、data 字段

#### Scenario: 拒绝写操作查询
- **WHEN** 调用 `execute_safe_select(sql="DELETE FROM users WHERE id = 1")`
- **THEN** 返回错误信息 "SQL包含禁止的关键字: delete"，不执行任何查询

#### Scenario: 拒绝 SELECT * 查询
- **WHEN** 调用 `execute_safe_select(sql="SELECT * FROM users")`
- **THEN** 返回错误信息提示必须明确指定列名

#### Scenario: 自动添加 TOP 限制
- **WHEN** 调用 `execute_safe_select(sql="SELECT id, name FROM users", limit=50)` 且 SQL 中无 TOP 子句
- **THEN** 系统自动将查询改写为 `SELECT TOP 50 id, name FROM users`

---

### Requirement: 故障诊断工具

系统 SHALL 在 `diagnostics.py` 中提供 MSSQL 故障诊断工具：

| 工具函数 | 功能描述 |
|----------|----------|
| `diagnose_slow_queries` | 诊断慢查询，使用 sys.dm_exec_query_stats |
| `diagnose_lock_conflicts` | 检测锁冲突和阻塞，使用 sys.dm_tran_locks |
| `diagnose_connection_issues` | 诊断连接问题，使用 sys.dm_exec_sessions |
| `check_database_health` | 数据库健康检查（状态、空间、备份） |

#### Scenario: 诊断慢查询
- **WHEN** 调用 `diagnose_slow_queries(threshold_ms=1000, limit=20)`
- **THEN** 返回平均执行时间超过 1000ms 的查询列表，包含查询文本、调用次数、平均/最大执行时间

#### Scenario: 检测锁冲突
- **WHEN** 存在活跃的锁等待时调用 `diagnose_lock_conflicts`
- **THEN** 返回阻塞关系列表，包含被阻塞的 session_id、阻塞者的 session_id、等待资源、等待时长

#### Scenario: 无锁冲突时返回空结果
- **WHEN** 无锁等待时调用 `diagnose_lock_conflicts`
- **THEN** 返回 `{"total_blocked_sessions": 0, "lock_conflicts": [], "has_conflicts": false}`

#### Scenario: 权限不足返回清晰错误
- **WHEN** 用户没有 VIEW SERVER STATE 权限时调用诊断工具
- **THEN** 返回错误信息 "需要 VIEW SERVER STATE 权限"

---

### Requirement: 监控指标采集工具

系统 SHALL 在 `monitoring.py` 中提供 MSSQL 监控指标采集工具：

| 工具函数 | 功能描述 |
|----------|----------|
| `get_database_metrics` | 获取数据库级别指标（大小、连接数、事务统计） |
| `get_instance_metrics` | 获取实例级别指标（CPU、内存、IO） |
| `get_wait_stats` | 获取等待统计信息 |

#### Scenario: 获取数据库指标
- **WHEN** 调用 `get_database_metrics`
- **THEN** 返回所有用户数据库的指标，包含 database_name、size_mb、active_connections、transactions_per_sec

#### Scenario: 获取实例性能指标
- **WHEN** 调用 `get_instance_metrics`
- **THEN** 返回 SQL Server 实例的性能指标，包含 cpu_usage、memory_usage_mb、buffer_cache_hit_ratio

#### Scenario: 获取等待统计
- **WHEN** 调用 `get_wait_stats(top_n=10)`
- **THEN** 返回前 10 个等待类型及其等待时间、等待次数

---

### Requirement: 工具函数文档规范

每个工具函数 SHALL 遵循以下文档规范：

- 使用中文 docstring 描述工具功能
- 包含 "**何时使用此工具:**" 段落说明使用场景
- 包含 "**工具能力:**" 段落说明功能范围
- Args 段落描述每个参数
- Returns 段落描述返回格式

#### Scenario: 工具描述符合 LangChain 规范
- **WHEN** 工具被加载到 LangChain agent
- **THEN** agent 可以正确理解工具的用途和参数，并在合适的场景调用

---

### Requirement: 错误处理规范

所有工具函数 SHALL 遵循统一的错误处理规范：

- 捕获数据库异常并返回 JSON 格式错误信息
- 错误信息包含 `error` 字段和描述性文本
- 连接错误包含服务器地址信息
- 权限错误提示所需权限
- 使用 loguru 记录错误日志

#### Scenario: 数据库连接错误
- **WHEN** 数据库连接失败
- **THEN** 返回 `{"error": "数据库连接失败: <详细原因>"}`

#### Scenario: 查询执行错误
- **WHEN** SQL 查询执行失败
- **THEN** 返回 `{"error": "查询执行失败: <详细原因>"}` 并回滚事务
