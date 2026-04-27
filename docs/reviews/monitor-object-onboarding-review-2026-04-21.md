# 监控对象接入与纳管 Code Review

审查基线：`origin/master` @ `4d11a80069e89ea7c64d974d34ba480866fe3ced`

范围：从 `server/apps/monitor/`、`server/apps/node_mgmt/` 出发，沿监控对象接入、节点配置下发、系统管理权限查询链路追踪到 RPC/NATS 与系统管理侧实现。

## 结论

本次发现 4 个值得升级处理的严重问题。核心风险不是代码风格，而是监控纳管入口把用户提交的 `node_ids`、`group_ids`、`config_id`、`current_team` 当作可信边界，导致越权纳管、跨租户配置读写，以及失败后仍推进“已纳管”状态。

## Findings

### P0: 监控接入入口未校验节点与组织权限，可越权纳管任意节点

证据：

- `server/apps/monitor/views/node_mgmt.py:45-52` 的 `batch_setting_node_child_config` 只记录用户名和 `current_team`，随后直接把 `request.data` 交给 `InstanceConfigService.create_monitor_instance_by_node_mgmt`。
- `server/apps/monitor/services/node_mgmt.py:401-453` 从请求体读取 `monitor_object_id`、`instances`、`group_ids`、`node_ids` 等数据并创建 `MonitorInstance`、组织关联和默认规则。
- `server/apps/monitor/utils/plugin_controller.py:208-229` 将请求派生出的 `node_id` 写入 node_mgmt 配置创建请求，最终在节点管理侧绑定采集配置。

影响：

任意已登录用户只要知道或枚举到节点 ID，就可以提交包含其他团队节点的 `node_ids` 与任意 `group_ids`，让监控侧创建实例、规则，并向节点管理侧下发采集配置。这会绕过节点管理的实例权限边界，造成跨团队纳管、错误绑定，甚至把采集任务投递到不属于当前用户的节点。

建议：

在监控接入入口同时校验监控配置权限与节点操作权限。`group_ids` 不应直接信任请求体，应从用户授权的 `current_team`/子团队派生；每个 `node_id` 必须通过 node_mgmt 权限过滤后再参与配置创建。拒绝部分未授权节点，且测试覆盖“跨团队 node_id / group_id 被拒绝”。

### P0: 采集配置读取和更新只按 ID 查找，缺少实例权限校验

证据：

- `server/apps/monitor/views/node_mgmt.py:60-70` 暴露 `get_config_content` 与 `update_instance_collect_config`，没有权限装饰器，也没有基于当前团队或实例授权的校验。
- `server/apps/monitor/services/node_mgmt.py:70-83` 只按 `CollectConfig.id` 获取配置，然后通过 `NodeMgmt().get_child_configs_by_ids` / `get_configs_by_ids` 返回节点管理侧配置内容。
- `server/apps/monitor/services/node_mgmt.py:470-484` 只确认 `CollectConfig` 存在，即调用 `NodeMgmt().update_config_content` / `update_child_config_content` 更新节点管理侧配置。

影响：

已登录用户如果拿到任意配置 ID，就可以读取其他团队监控采集配置内容，或修改其节点采集配置。由于配置内容和 `env_config` 可能包含连接地址、账号、token、password 派生变量等敏感运行参数，这同时是横向越权与配置篡改风险。

建议：

所有配置 ID 必须先反查 `CollectConfig -> MonitorInstance -> MonitorInstanceOrganization`，并使用与监控实例一致的权限模型校验 `View`/`Operate`。node_mgmt 的 NATS 配置读写接口也应增加调用方上下文或服务端二次校验，避免内部接口默认可信。

### P0: 监控调用系统管理查询时信任客户端 cookie，可跨团队读取用户与通知通道

证据：

- `server/apps/monitor/views/system_mgmt.py:9-20` 直接读取客户端 cookie 中的 `current_team` 和 `include_children`，然后调用系统管理查询用户和通知通道。
- `server/apps/system_mgmt/nats_api.py:281-296` 的 `get_group_users` 仅按传入 `group`/`include_children` 查询用户列表，不接收也不校验调用用户。
- `server/apps/system_mgmt/nats_api.py:440-486` 的 `search_channel_list` 仅按传入团队及子团队过滤通道，同样没有用户上下文校验。

影响：

已登录用户可以伪造 `current_team=<任意组织ID>` 和 `include_children=1`，通过监控模块读取其他组织及其子组织的用户列表、通知通道名称和通道类型。这破坏了系统管理侧的团队边界，也会影响监控策略通知人、通知渠道选择等后续操作。

建议：

监控侧不应把 cookie 里的团队 ID 当作授权事实。调用系统管理前必须校验当前用户属于该团队或有继承授权；更稳妥的是把 `username/domain/current_team/include_children` 传给系统管理侧，由系统管理在 NATS API 内统一做团队授权过滤。

### P1: 接入流程存在假成功，模板缺失或渲染失败后仍提交已纳管状态

证据：

- `server/apps/monitor/services/node_mgmt.py:437-454` 先在事务中创建实例、组织关联和默认规则，再调用 `Controller(data).controller()`。
- `server/apps/monitor/utils/plugin_controller.py:167-173` 在没有模板或没有可创建配置时只记录 warning/debug 后 `return`，不会抛错。
- `server/apps/monitor/utils/plugin_controller.py:183-206` 单个配置类型模板缺失或渲染失败时 `continue`，最终可能只创建部分配置，甚至没有任何配置。
- `server/apps/monitor/utils/plugin_controller.py:258-265` 节点管理配置创建通过 RPC/NATS 进入另一个事务域，监控侧事务无法回滚已经在节点管理侧成功落库的配置。

影响：

用户可能收到成功响应，但监控侧只有实例和分组规则，没有对应采集配置；或者只有部分节点、部分配置成功。后续列表会显示对象已接入，实际采集链路缺失，形成脏状态、漏纳管和重复接入风险。跨服务 RPC 成功后如果监控侧提交失败，也会留下 node_mgmt 孤儿配置。

建议：

接入流程应 fail closed：预先校验模板、节点、配置类型和预期配置数量，任何实例无法生成完整配置时直接失败；渲染失败不能静默跳过。跨服务写入需要显式 saga/补偿任务或幂等 reconcile 任务，至少记录可重放的接入任务状态与失败原因。

## 建议补充的最小测试

- `batch_setting_node_child_config`：普通用户提交非授权 `node_ids` / `group_ids` 时返回 403。
- `get_config_content` / `update_instance_collect_config`：跨团队配置 ID 不可读写；同团队 `View` 只能读，`Operate` 才能写。
- `SystemMgmtView`：伪造其他团队 `current_team` 或 `include_children=1` 时不可返回用户/通道。
- 接入模板缺失、渲染失败、部分节点配置失败时，监控实例、规则、`CollectConfig` 不应进入成功态，或必须生成可补偿失败任务。
