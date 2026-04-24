## Context

OpsPilot 的 Metis 智能体目前通过 `server/apps/opspilot/metis/llm/tools/` 目录管理各类运维工具。PostgreSQL 工具已经实现了完整的数据库运维能力（8个子模块，40+工具函数），采用 `psycopg2` 作为驱动，通过 `@tool` 装饰器暴露 LangChain 工具。

当前架构特点：
- **工具加载**: `tools_loader.py` 通过 `TOOL_MODULES` 字典静态注册工具模块
- **连接管理**: 每个工具模块有独立的 `utils.py` 管理连接，使用 `RunnableConfig` 传递配置参数
- **安全机制**: 动态 SQL 工具实现了安全验证（禁止写操作、敏感字段过滤）
- **参数配置**: 通过 `CONSTRUCTOR_PARAMS` 元数据定义工具集的构造参数

项目中已存在 MSSQL 连接示例：`agents/stargazer/plugins/inputs/mssql/mssql_info.py` 使用 `pyodbc` 连接 MSSQL。

## Goals / Non-Goals

**Goals:**
- 实现 MSSQL 工具模块，与 PostgreSQL 工具保持一致的架构和使用体验
- 提供核心运维能力：资源查询、动态 SQL、故障诊断、监控指标
- 复用现有工具模式，最小化代码改动
- 使用 pyodbc 作为 MSSQL 驱动（项目已有使用先例）

**Non-Goals:**
- 不实现 PostgreSQL 特有功能（如 pg_stat_statements、WAL 监控等）
- 不实现 MSSQL 高级特性（如 AlwaysOn、Replication 详细监控）
- 不修改现有 PostgreSQL 工具的实现
- 不支持 SQL Server 2014 以下版本

## Decisions

### 1. 驱动选择：pyodbc

**决定**: 使用 `pyodbc>=5.2.0` 作为 MSSQL 连接驱动

**理由**:
- 项目中 `stargazer` 模块已使用 pyodbc 连接 MSSQL，有现成的使用模式
- pyodbc 是 ODBC 标准实现，稳定性好、兼容性强
- 支持 SQL Server 2016+ 的所有功能

**备选方案**:
- `pymssql`: 纯 Python 实现，不需要 ODBC 驱动，但功能受限、维护不活跃
- `sqlalchemy`: 抽象层过重，不适合直接执行原生 SQL 查询

### 2. 模块结构：精简的 PostgreSQL 模式

**决定**: 采用精简的模块结构（5个子模块）

```
mssql/
├── __init__.py      # 工具集入口、CONSTRUCTOR_PARAMS、导出
├── utils.py         # 连接管理、通用工具函数
├── resources.py     # 基础资源查询（数据库/表/索引/Schema/角色）
├── dynamic.py       # 动态 SQL 安全查询
├── diagnostics.py   # 故障诊断（慢查询/锁/连接）
└── monitoring.py    # 监控指标采集
```

**理由**:
- MSSQL 系统视图与 PostgreSQL 不同，部分功能无法直接映射
- 精简模块降低初始实现复杂度，后续可按需扩展
- 保留核心运维能力，满足 80% 使用场景

**PostgreSQL 模块未映射**:
- `optimization.py`: MSSQL 优化建议需要不同的系统视图
- `tracing.py`: 依赖 Extended Events，实现复杂度高
- `analysis.py`: 部分功能可合并到 diagnostics

### 3. 连接管理模式

**决定**: 复用 PostgreSQL 的 `prepare_context` + `get_db_connection` 模式

```python
CONSTRUCTOR_PARAMS = [
    {"name": "host", "type": "string", "required": False, "description": "MSSQL服务器地址,默认localhost"},
    {"name": "port", "type": "integer", "required": False, "description": "端口,默认1433"},
    {"name": "database", "type": "string", "required": False, "description": "默认连接的数据库"},
    {"name": "user", "type": "string", "required": False, "description": "用户名"},
    {"name": "password", "type": "string", "required": False, "description": "密码"},
]
```

**理由**: 保持与 PostgreSQL 工具一致的配置体验，用户无需学习新的参数模式

### 4. ODBC 驱动配置

**决定**: 使用 "ODBC Driver 17 for SQL Server" 作为默认驱动，支持配置覆盖

**理由**:
- Driver 17 是微软推荐的最新稳定版本
- 支持 TLS 1.2、AlwaysOn 等现代特性
- 允许通过环境变量或配置覆盖驱动名称

### 5. 系统视图映射

**决定**: 使用 MSSQL 原生系统视图和 DMV（Dynamic Management Views）

| PostgreSQL | MSSQL |
|------------|-------|
| `pg_database` | `sys.databases` |
| `pg_tables` | `INFORMATION_SCHEMA.TABLES` |
| `pg_indexes` | `sys.indexes` + `sys.index_columns` |
| `pg_stat_activity` | `sys.dm_exec_sessions` + `sys.dm_exec_requests` |
| `pg_locks` | `sys.dm_tran_locks` |
| `pg_stat_statements` | `sys.dm_exec_query_stats` |

## Risks / Trade-offs

**[Risk] ODBC 驱动依赖**
→ 需要在运行环境安装 ODBC Driver 17 for SQL Server，增加部署复杂度
→ **Mitigation**: 文档中明确系统依赖，提供 Docker 镜像配置示例

**[Risk] SQL 方言差异**
→ MSSQL 的 T-SQL 与 PostgreSQL 语法有显著差异，动态 SQL 验证逻辑需要调整
→ **Mitigation**: 在 `dynamic.py` 中实现 MSSQL 特定的 SQL 安全验证函数

**[Risk] 权限要求**
→ 部分 DMV 需要 VIEW SERVER STATE 权限
→ **Mitigation**: 工具描述中标注权限要求，返回清晰的权限不足错误信息

**[Trade-off] 功能覆盖度**
→ 初始版本不包含所有 PostgreSQL 工具的对等功能
→ 优先实现高频使用的核心功能，后续根据用户反馈迭代

**[Trade-off] 只读事务**
→ MSSQL 不支持 PostgreSQL 的 `BEGIN TRANSACTION READ ONLY` 语法
→ 使用 `SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED` 或 snapshot isolation 替代
