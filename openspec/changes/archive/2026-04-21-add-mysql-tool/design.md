## Context

OpsPilot 的 LLM 工具体系已包含 PostgreSQL（44 个工具，单实例模式）、MSSQL（37 个工具，单实例模式）和 Redis（60+ 个工具，多实例模式）。MySQL 工具需要同时借鉴两个方向：

- **工具分类与 SQL 安全机制**：沿用 postgres/mssql 的子模块划分（resources、dynamic、diagnostics、monitoring、optimization、analysis）和 `validate_sql_safety()` 安全校验
- **多实例批量执行架构**：沿用 Redis 的 `NormalizedCredentials` + `execute_with_credentials()` 机制，通过 `common/credentials.py` 统一调度

当前 MSSQL 和 PostgreSQL 工具仍为单实例模式（`CONSTRUCTOR_PARAMS` 为平铺的 host/port/user/password 字段）。MySQL 工具从设计之初就采用多实例模式。

## Goals / Non-Goals

**Goals:**
- 提供 35 个 MySQL 运维工具，覆盖资源发现、动态查询、故障诊断、运行监控、优化建议、性能分析
- 支持多实例配置，不指定实例时批量巡检所有实例
- 支持 `instance_name` / `instance_id` 参数定向单个实例
- 兼容旧单实例平铺字段配置（legacy 模式）
- SQL 注入防护和只读事务保护

**Non-Goals:**
- 不改造现有 PostgreSQL/MSSQL 工具为多实例模式（后续单独变更）
- 不支持 MySQL 写操作（INSERT/UPDATE/DELETE）
- 不提供前端 UI 编辑器（本次仅后端工具层）
- 不支持 MySQL Group Replication / InnoDB Cluster 高级拓扑管理

## Decisions

### Decision 1: 驱动选择 `mysql-connector-python`

**选择**: `mysql-connector-python`（Oracle 官方维护）
**替代方案**: `pymysql`（纯 Python，社区维护）、`mysqlclient`（C 扩展，需编译环境）

**理由**:
- 纯 Python 实现，无需 C 编译环境，与仓库 Docker 构建流程兼容
- Oracle 官方维护，MySQL 8.x 新特性支持及时
- MCP Server 参考项目也使用此驱动，验证了可行性
- 支持 `charset`/`collation`/`sql_mode` 的细粒度配置

### Decision 2: 多实例架构复用 Redis 的 credentials 模式

**选择**: 复用 `common/credentials.py` 的 `NormalizedCredentials` + `execute_with_credentials()` + `CredentialAdapter` 协议

**替代方案**: 独立实现多实例管理（如 MSSQL/PG 当前的单实例模式）

**理由**:
- Redis 已验证该模式可稳定工作
- `execute_with_credentials()` 的单/多分发逻辑是通用的，无需重复实现
- `MysqlCredentialAdapter` 只需实现 4 个方法即可接入
- 保持工具体系内部一致性，后续 PG/MSSQL 升级多实例也可复用

### Decision 3: 只读保护策略

**选择**: 使用 `SET SESSION TRANSACTION READ ONLY` + `validate_sql_safety()` 双重防护

**替代方案**: 仅靠 `validate_sql_safety()` 关键词黑名单

**理由**:
- MySQL 5.6.5+ 支持 `SET SESSION TRANSACTION READ ONLY`，在数据库层面阻止写操作
- `validate_sql_safety()` 在应用层拦截危险 SQL（`DROP`/`ALTER`/`LOAD`/`FLUSH` 等）
- 双重防护比单一防护更安全

### Decision 4: MySQL 特有的禁止关键词列表

在通用禁止词（`DROP`/`ALTER`/`TRUNCATE`/`CREATE`/`GRANT`/`REVOKE`/`INSERT`/`UPDATE`/`DELETE`）基础上，新增 MySQL 特有：

```
LOAD, HANDLER, FLUSH, PURGE, RESET, CHANGE, INSTALL, UNINSTALL,
PREPARE, EXECUTE, DEALLOCATE, KILL, LOCK, UNLOCK
```

### Decision 5: 文件结构

```
mysql/
├── __init__.py          CONSTRUCTOR_PARAMS(多实例) + 导入 + __all__
├── connection.py        MysqlCredentialAdapter + 连接管理 + 实例提示
├── utils.py             prepare_context + 公共函数 + validate_sql_safety
├── resources.py         8 个工具（资源发现）
├── dynamic.py           5 个工具（动态查询）
├── diagnostics.py       7 个工具（故障诊断）
├── monitoring.py        8 个工具（运行监控）
├── optimization.py      4 个工具（优化建议）
└── analysis.py          3 个工具（性能分析）
```

### Decision 6: CONSTRUCTOR_PARAMS 设计

```python
CONSTRUCTOR_PARAMS = [
    {"name": "mysql_instances", "type": "string", "required": False,
     "description": "MySQL多实例JSON配置"},
    {"name": "mysql_default_instance_id", "type": "string", "required": False,
     "description": "默认MySQL实例ID"},
]
```

实例字段：`id`, `name`, `host`, `port`(3306), `database`(mysql), `user`, `password`, `charset`(utf8mb4), `collation`(utf8mb4_unicode_ci), `ssl`, `ssl_ca`, `ssl_cert`, `ssl_key`

### Decision 7: 连接配置借鉴 MCP Server

从 `designcomputer/mysql_mcp_server` 借鉴以下连接配置实践：
- 默认 `charset=utf8mb4`，`collation=utf8mb4_unicode_ci`（避免不同 MySQL 版本的 utf8mb4_0900_ai_ci 兼容问题）
- `autocommit=True`（只读工具无需手动事务管理）
- `sql_mode` 可配置（默认 `TRADITIONAL`）

### Decision 8: 工具注册

在 `tools_loader.py` 中新增：
```python
from apps.opspilot.metis.llm.tools import mysql
# ...
"mysql": (mysql, False),
```

`enable_extra_prompt=False`，与 postgres/mssql 一致。多实例提示通过 `get_mysql_instances_prompt()` 注入。

## Risks / Trade-offs

**[Risk] mysql-connector-python 性能不如 mysqlclient** → 本工具面向运维诊断场景，非高并发查询，纯 Python 驱动的性能足够。若后续有性能瓶颈，可替换为 mysqlclient，连接接口兼容。

**[Risk] 批量巡检多实例时某个实例超时拖慢整体** → `execute_with_credentials()` 已实现 per-instance 异常捕获，单个实例失败不影响其他实例结果。可后续增加连接超时配置（`connect_timeout`）。

**[Risk] MySQL 5.x 与 8.x 的 SQL 兼容性差异** → 部分诊断 SQL 依赖 `performance_schema`（5.6+ 默认启用）和 `sys` schema（5.7+ 内置）。工具内部需对不支持的查询做 graceful fallback，返回提示而非报错。

**[Risk] 旧单实例配置升级到多实例** → 通过 `MysqlCredentialAdapter` 的 `build_from_flat_config` 支持 legacy 平铺字段，与 Redis 的升级策略一致。

**[Trade-off] 35 个工具 vs 更少的工具集** → 工具数量多但语义明确，LLM 可精确选择。比单一 `execute_sql` 更安全可控，代价是实现工作量较大。
