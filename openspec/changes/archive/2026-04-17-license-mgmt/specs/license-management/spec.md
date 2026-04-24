## ADDED Requirements

### Requirement: 许可管理页面必须通过稳定设置路由加载企业版实现

系统 MUST 保留 `/system-manager/settings/license` 作为稳定访问路径，并由该路径加载企业版许可管理页面实现。

#### Scenario: 公共设置页访问许可页
- **WHEN** 用户访问 `/system-manager/settings/license`
- **THEN** 系统 MUST 通过公共路由壳加载 enterprise 许可管理页面，而不是在公共页内直接实现许可业务

#### Scenario: 许可页使用统一弹窗组件
- **WHEN** 页面展示“添加许可”或“设置许可提醒”弹窗
- **THEN** 系统 MUST 使用仓库现有 `OperateModal` 组件承载弹窗交互

### Requirement: 许可管理必须支持当前许可与历史许可治理

系统 MUST 支持注册码读取、许可导入、生效许可列表、历史许可列表、许可停用与模块授权摘要展示。

#### Scenario: 管理员读取注册码并添加许可
- **WHEN** 管理员打开“添加许可”弹窗并提交有效许可码
- **THEN** 系统 MUST 返回当前注册码展示值、完成许可验签和导入，并在成功后刷新许可列表

#### Scenario: 管理员停用当前许可
- **WHEN** 管理员对生效许可执行停用操作
- **THEN** 该许可 MUST 从生效列表移除，并出现在历史许可列表中

#### Scenario: 页面展示模块授权摘要
- **WHEN** 许可管理页面加载模块摘要
- **THEN** 系统 MUST 返回免激活、已激活、未激活模块状态及数量汇总

### Requirement: 许可卡片风险样式必须跟随服务端提醒状态

系统 MUST 由服务端返回的提醒状态驱动许可卡片风险展示，而不是仅依赖页面本地剩余天数推断。

#### Scenario: 许可进入提醒窗口
- **WHEN** 许可剩余有效期小于等于当前提醒天数
- **THEN** 许可列表项中的 `reminder.status` MUST 返回 `warning`，页面 MUST 使用预警样式展示卡片和剩余天数标签

#### Scenario: 许可未进入提醒窗口
- **WHEN** 许可剩余有效期大于当前提醒天数
- **THEN** 许可列表项中的 `reminder.status` MUST 返回 `healthy`，页面 MUST 使用健康样式展示卡片和剩余天数标签

### Requirement: 提醒配置必须统一支持默认、单许可、节点和日志容量场景

系统 MUST 提供统一的通知渠道、通知人员、提醒时间或阈值配置能力，并在不同提醒场景中按既定模式回显。

#### Scenario: 修改默认提醒
- **WHEN** 管理员在默认提醒面板修改通知渠道、通知人员或默认提醒时间
- **THEN** 系统 MUST 保存全局默认提醒并在后续跟随默认的场景中使用该结果

#### Scenario: 单许可切换到单独配置
- **WHEN** 管理员在许可提醒弹窗选择 `custom`
- **THEN** 系统 MUST 允许维护该许可独立的渠道、人员和提醒时间，并在保存后按独立配置回显

#### Scenario: 单许可保持跟随默认
- **WHEN** 管理员在许可提醒弹窗选择 `follow`
- **THEN** 系统 MUST 展示默认提醒摘要，并忽略该许可上的独立渠道、人员和提醒时间值

#### Scenario: 节点提醒维护默认阈值和对象覆盖
- **WHEN** 管理员保存模块节点提醒配置
- **THEN** 系统 MUST 保存模块级阈值，并允许按 `object_type` 保存专用节点覆盖项

#### Scenario: 日志容量提醒切换模式
- **WHEN** 管理员在日志容量提醒中切换 `follow/custom`
- **THEN** 系统 MUST 在 `follow` 模式展示默认摘要，在 `custom` 模式保存日志独立通知渠道、通知人员和容量阈值

### Requirement: 提醒配置的用户和渠道必须限制在当前可见范围

系统 MUST 在提醒配置保存前校验通知渠道和通知人员是否处于当前用户可见范围内。

#### Scenario: 提交不可见渠道
- **WHEN** 请求中包含当前用户不可见的 `channel_ids`
- **THEN** 系统 MUST 拒绝保存该提醒配置

#### Scenario: 提交不可见用户
- **WHEN** 请求中包含当前用户不可见的 `user_ids`
- **THEN** 系统 MUST 拒绝保存该提醒配置

### Requirement: 受控新增资源入口必须经过许可校验

系统 MUST 对命中 `LICENSE_APP_PERMISSIONS` 的新增资源请求执行统一许可校验。

#### Scenario: 许可校验未启用
- **WHEN** `LICENSE_MGMT_ENABLED` 为 `False`
- **THEN** 许可校验中间件 MUST 直接放行请求

#### Scenario: 请求命中受控新增入口且无有效许可
- **WHEN** 请求命中 `LICENSE_APP_PERMISSIONS` 中定义的新增入口，且 RPC 校验返回 `allowed=False`
- **THEN** 中间件 MUST 返回 403，并附带拒绝原因

#### Scenario: 请求命中受控新增入口且许可有效
- **WHEN** 请求命中 `LICENSE_APP_PERMISSIONS` 中定义的新增入口，且 RPC 校验返回 `allowed=True`
- **THEN** 中间件 MUST 放行请求
