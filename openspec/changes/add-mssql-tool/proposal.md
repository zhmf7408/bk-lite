## Why

OpsPilot 的 Metis 智能体当前支持 PostgreSQL 数据库运维工具，但缺少对 Microsoft SQL Server (MSSQL) 的支持。企业用户普遍存在 MSSQL 数据库运维需求，新增 MSSQL 工具可以扩展 Metis 的数据库运维能力覆盖面，满足更多企业用户场景。

## What Changes

- 新增 `mssql` 工具模块，位于 `server/apps/opspilot/metis/llm/tools/mssql/`
- 参考 PostgreSQL 工具实现，提供完整的 MSSQL 运维工具集：
  - 基础资源查询（数据库、表、索引、Schema、角色）
  - 动态 SQL 安全查询
  - 故障诊断（慢查询、锁、连接问题）
  - 性能分析（配置、统计信息）
  - 监控指标采集
- 在 `tools_loader.py` 的 `TOOL_MODULES` 中注册 `mssql` 工具
- 新增 `pyodbc` 依赖到 server 的 `pyproject.toml`（opspilot optional-dependencies）

## Capabilities

### New Capabilities

- `mssql-tool`: Microsoft SQL Server 数据库运维工具集，包括资源查询、动态 SQL 执行、故障诊断、性能分析和监控指标采集功能

### Modified Capabilities

（无需修改现有能力）

## Impact

**代码变更:**
- 新增目录: `server/apps/opspilot/metis/llm/tools/mssql/`
- 修改文件: `server/apps/opspilot/metis/llm/tools/tools_loader.py`
- 修改文件: `server/apps/opspilot/metis/llm/tools/__init__.py`

**依赖变更:**
- 新增 `pyodbc>=5.2.0` 到 `server/pyproject.toml` 的 `[project.optional-dependencies] opspilot` 部分

**系统要求:**
- 需要在运行环境安装 ODBC Driver 17 for SQL Server（或更高版本）

**API 兼容性:**
- 新增工具，不影响现有 API
- 遵循现有工具的 CONSTRUCTOR_PARAMS 模式，支持 host、port、database、user、password 配置
