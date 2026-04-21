## Why

OpsPilot 已有 PostgreSQL、MSSQL、Redis 等数据库工具，但缺少 MySQL 工具。MySQL 是国内使用最广泛的关系型数据库之一，用户需要通过 LLM 对 MySQL 实例进行巡检、诊断、查询和优化。同时参照 Redis 工具的多实例架构，MySQL 工具需从设计之初就支持批量连接多个实例，实现一次调用巡检所有 MySQL 实例。

## What Changes

- 新增 `server/apps/opspilot/metis/llm/tools/mysql/` 工具包，包含约 35 个子工具，覆盖资源发现、动态查询、故障诊断、运行监控、优化建议、性能分析六大类
- 新增 MySQL 多实例连接管理（`connection.py`），复用 `common/credentials.py` 的 `NormalizedCredentials` + `execute_with_credentials()` 批量执行机制
- 在 `tools_loader.py` 中注册 `mysql` 工具模块
- 新增 `mysql-connector-python` 依赖
- 所有工具支持 `instance_name` / `instance_id` 参数，不指定时对所有已配置实例批量执行

## Capabilities

### New Capabilities
- `mysql-tool-multi-instance`: MySQL 工具的多实例配置、连接管理、批量执行能力，以及 35 个子工具（资源发现、动态查询、故障诊断、运行监控、优化建议、性能分析）

### Modified Capabilities
（无需修改现有 spec）

## Impact

- **代码**: `server/apps/opspilot/metis/llm/tools/` 新增 `mysql/` 目录（约 9 个文件）；`tools_loader.py` 新增注册项
- **依赖**: `server/pyproject.toml` 新增 `mysql-connector-python`
- **API**: 无外部 API 变更，工具通过现有 `tools_loader` 机制暴露给 LLM
- **安全**: 所有查询经过 `validate_sql_safety()` 校验，支持 `SET SESSION TRANSACTION READ ONLY`，敏感字段屏蔽
- **兼容性**: 纯新增功能，不影响现有工具
