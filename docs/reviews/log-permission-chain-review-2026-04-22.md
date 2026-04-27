# 日志权限链路严重技术债务审查

## 结论

日志分组权限当前只约束了分组列表可见性，没有被复用到日志检索、字段枚举、统计、tail，以及分组写操作链路中。日志业务权限模型因此形成了“列表看起来受限，实际查询和管理仍可越范围”的断层。

这属于代码与业务逻辑层的权限问题，不涉及 Kubernetes、数据库账号、VMLogs 集群账号、NATS ACL、云平台 IAM 或网络隔离等基础设施权限。

## 核心问题

### 1. 日志 search 只校验分组存在，不校验用户是否有权使用该分组

`server/apps/log/views/search.py` 的 `search`、`hits`、`top_stats`、`tail` 入口都只调用 `LogGroupQueryBuilder.validate_log_groups(log_groups)`。该校验只确认分组 ID 存在，随后直接把用户传入的分组交给 `SearchService` 查询。

关键证据：

- `server/apps/log/views/search.py:47-57`：`search` 从请求体读取 `log_groups`，只做存在性校验后执行查询。
- `server/apps/log/views/search.py:71-81`：`hits` 同样只做存在性校验。
- `server/apps/log/views/search.py:91-104`：`top_stats` 同样只做存在性校验。
- `server/apps/log/views/search.py:113-131`：`tail` 只要求传入 `log_groups`，但不校验分组归属或权限。
- `server/apps/log/utils/log_group.py:205-220`：`validate_log_groups` 只查询 `LogGroup.objects.filter(id__in=log_group_ids)` 并比较缺失 ID，没有结合当前用户、当前组织或权限规则。

影响：

只要调用者知道或猜到某个日志分组 ID，就可以把该分组作为日志搜索范围使用；接口层没有验证该分组是否属于当前组织、是否在用户授权范围内、是否允许被当前用户用于 search。日志分组从“权限边界”退化成了“可控查询条件”。

### 2. 空分组和 default 分组会回退为全量查询，形成越范围检索旁路

`LogGroupQueryBuilder.build_query_with_groups` 对空分组和 `default` 分组采用放大范围的默认行为：

- 没有传 `log_groups` 时直接返回用户原始查询。
- 包含 `default` 时直接返回用户原始查询或 `*`，并忽略其他分组。
- 分组规则为空时认为是“查询所有日志”，不注入任何限制条件。
- 分组规则转换失败时跳过该分组；如果最终没有有效条件，也会回退到用户原始查询。

关键证据：

- `server/apps/log/utils/log_group.py:79-96`：空分组和 `default` 分组直接返回用户查询。
- `server/apps/log/utils/log_group.py:101-108`：有效分组为空或无条件时返回用户查询。
- `server/apps/log/utils/log_group.py:131-142`：空规则和规则转换异常都跳过分组条件。
- `server/apps/log/utils/log_group.py:153-155`：没有有效分组条件时返回用户查询或 `*`。

影响：

日志 search、hits、top_stats、all_attrs、tail 都依赖同一个查询构造器。任何入口只要缺失分组、传入 `default`、使用空规则分组，或触发规则转换失败，就可能绕过分组范围限制，导致“看起来选择了分组，底层实际没有范围约束”。

### 3. 字段枚举和属性发现接口同样绕过分组权限，可能泄露日志字段与业务标签

字段枚举不是普通元数据查询，它会暴露日志中存在的字段、标签、业务对象标识或敏感字段名。当前实现没有把字段枚举纳入与 search 相同的授权边界。

关键证据：

- `server/apps/log/views/search.py:14-24`：`field_values` 只读取字段名和时间范围，直接调用 `SearchService.field_values`，没有接收或校验日志分组。
- `server/apps/log/services/search.py:39-47`：`field_values` 直接查询 VictoriaLogs 字段值。
- `server/apps/log/views/collect_config.py:158-172`：`all_attrs` 虽然接收 `log_groups`，但仍只做存在性校验。
- `server/apps/log/services/search.py:55-60`：`all_field_names` 复用同一个无权限上下文的分组查询构造器。

影响：

即使日志明细查询后续收紧，字段枚举和属性发现仍会成为侧向泄露入口，暴露用户无权日志范围内的字段结构、标签值和可用于进一步构造查询的线索。

### 4. 日志分组管理写操作没有复用列表权限，且组织绑定完全信任请求参数

`LogGroupViewSet.list` 会通过 `get_permission_rules` + `permission_filter` 做可见性过滤，但 `create`、`update`、`destroy` 直接基于全量 queryset 操作对象。序列化器允许请求方直接提交 `organizations`，只校验它们是整数，不校验当前用户是否有权把分组绑定到这些组织。

关键证据：

- `server/apps/log/views/log_group.py:47-86`：只有列表接口使用日志分组权限过滤。
- `server/apps/log/views/log_group.py:36-45`：创建接口没有权限检查，直接保存分组。
- `server/apps/log/views/log_group.py:88-99`：更新接口通过 `self.get_object()` 从全量 queryset 取对象并保存。
- `server/apps/log/views/log_group.py:101-111`：删除接口同样从全量 queryset 取对象并删除。
- `server/apps/log/serializers/log_group.py:43-51`：创建时直接按请求中的 `organizations` 建立分组组织关系。
- `server/apps/log/serializers/log_group.py:59-69`：更新时先删除原组织关系，再按请求参数重建。
- `server/apps/log/serializers/log_group.py:73-81`：组织字段只做类型校验。

影响：

分组管理权限与 search 使用权限脱钩。低权限用户可能创建或修改指向其他组织/范围的日志分组，再通过 search 链路使用该分组查询日志，形成“管理入口污染权限边界，查询入口放大影响”的组合风险。

## 为什么本次不直接修复

这是链路级权限模型问题，不是单个接口补一行校验能安全解决：

- 需要明确日志 search、字段枚举、统计、tail、分组管理、告警策略使用日志分组时的统一权限语义。
- 需要决定空分组、default 分组、空规则分组、规则解析失败时的 deny-by-default 行为。
- 需要把当前用户、当前组织、include_children、日志分组实例权限和组织范围传递到查询构造层。
- 需要补齐 search、hits、top_stats、tail、field_values、all_attrs、分组 CRUD、搜索条件保存、策略引用日志分组等入口的统一测试。

如果只在某几个 view 中临时过滤，容易留下字段枚举、统计或策略扫描等旁路，甚至让不同入口产生不一致的权限结果。因此本次先提交审查文档，供负责人确认权限模型后再做集中修复。

## 建议修复方向

1. 为日志模块定义统一的 `LogSearchScope` 或等价服务，输入当前用户、当前组织、include_children 和请求分组，输出可用于查询层的授权分组与强制范围条件。
2. `validate_log_groups` 不再只做存在性校验，必须校验分组归属、实例权限和组织范围；未授权分组应拒绝，而不是静默跳过。
3. search、hits、top_stats、tail、field_values、all_attrs 必须统一走同一个授权范围构造器，禁止无授权上下文直接查询 VictoriaLogs。
4. 空分组、default 分组、空规则、规则解析失败默认拒绝或降级为当前用户最小授权范围，禁止回退到全量查询。
5. 日志分组 create/update/destroy 必须校验操作权限和组织绑定权限，`get_queryset` 应返回当前用户可操作范围，而不是全量 `LogGroup.objects.all()`。
6. 搜索条件和告警策略保存时校验引用的日志分组是否在当前用户授权范围内，避免把越权分组固化为后续执行范围。
7. 增加覆盖越权场景的测试：未授权分组 ID、空分组、default 分组、空规则、字段枚举、聚合统计、tail、分组组织绑定变更。
