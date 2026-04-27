# 日志权限链路修复方案

## 目标

把日志分组从“仅用于列表展示的筛选条件”收敛为“日志查询、字段枚举、分组管理、搜索条件保存时统一复用的授权边界”。

## 修复原则

1. **统一授权入口**：所有依赖 `log_groups` 的入口统一通过 `LogAccessScopeService` 解析当前用户、当前组织、`include_children` 和可访问日志分组。
2. **拒绝放宽回退**：当分组为空、规则为空、规则转换失败或传入未授权分组时，不再回退到原始全量查询。
3. **查询与管理共用同一权限上下文**：日志 search / hits / top_stats / tail / 字段枚举 / all_attrs / log_group CRUD / search_condition 保存，全部基于同一授权范围判断。
4. **最小兼容变更**：保留现有接口结构；`default` 和空 `log_groups` 在查询类接口中解释为“当前用户有权访问的全部日志分组”，而不是全量日志。

## 本次落地范围

### 1. 新增统一授权解析层

- 新增 `server/apps/log/services/access_scope.py`
- 负责：
  - 基于 `current_team` + `include_children` + 日志分组权限规则，解析可访问日志分组
  - 校验请求中的 `log_groups` 是否越权
  - 校验日志分组绑定的 `organizations` 是否越权

### 2. 收口读链路

- `search`
- `hits`
- `top_stats`
- `tail`
- `field_values`
- `field_names`
- `collect_types/all_attrs`

这些接口全部先解析授权分组，再进入查询层。

### 3. 收口管理链路

- `LogGroupViewSet.get_queryset()` 改为权限过滤后的 queryset
- `update` / `destroy` / `retrieve` 自动继承权限范围
- `LogGroupSerializer` 创建/更新时校验 `organizations` 绑定范围

### 4. 收口持久化引用

- `SearchConditionSerializer` 校验 `condition.log_groups` 时使用当前请求授权范围
- `PolicySerializer` 校验 `log_groups` 时优先使用当前请求授权范围

## 语义调整

1. 查询接口未传 `log_groups`：
   - 旧行为：原始查询直接下发
   - 新行为：扩展为当前用户有权访问的全部日志分组

2. 查询接口传 `default`：
   - 旧行为：原始查询直接下发
   - 新行为：扩展为当前用户有权访问的全部日志分组

3. 分组规则为空 / 转换失败：
   - 旧行为：回退为原始查询
   - 新行为：构造拒绝查询，避免放宽范围

4. 传入未授权分组：
   - 旧行为：只校验存在性，可能继续使用
   - 新行为：明确拒绝

## 风险与回滚

### 风险

- 历史上依赖“空分组/`default` 查全量”的调用会缩小结果范围
- 历史上保存了未授权分组的搜索条件/策略在更新时可能被拒绝

### 回滚

本次改动集中在日志模块授权解析层与调用点，可通过回退本次提交整体撤销；不会引入新的存储结构。

## 验证

1. 定向 pytest 覆盖：
   - 查询接口自动扩展授权分组
   - 未授权分组拒绝
   - 日志分组 CRUD 权限收口
   - 搜索条件权限校验
2. Django LSP diagnostics 无新增错误
3. `server/apps/log` 相关 pytest 通过
