## 1. License domain and route entry

- [x] 1.1 保留 `/system-manager/settings/license` 作为稳定入口，并将真实页面实现放到 enterprise 许可页中。
- [x] 1.2 建立 `server/apps/license_mgmt` 独立领域模型、服务与中间件基础结构。

## 2. License data flow

- [x] 2.1 支持注册码读取、许可导入、当前许可列表、历史许可列表和许可停用。
- [x] 2.2 提供模块授权摘要、CMDB/监控节点额度聚合、日志容量聚合结果供前端展示。
- [x] 2.3 在许可列表返回中补充提醒状态字段，供前端直接渲染健康/预警样式。

## 3. Reminder governance

- [x] 3.1 支持全局默认提醒配置的读取、保存与页面内联编辑。
- [x] 3.2 支持单许可提醒的 `follow/custom` 模式切换、回显与保存。
- [x] 3.3 支持节点提醒阈值、专用节点覆盖项和日志容量提醒的读取与保存。
- [x] 3.4 对提醒配置中的通知渠道和通知人员执行可见范围校验。

## 4. Guard and scheduled behaviors

- [x] 4.1 支持根据 `LICENSE_APP_PERMISSIONS` 匹配新增资源请求，并通过中间件触发统一许可校验。
- [x] 4.2 支持通过 RPC 返回模块新增资源是否允许的校验结果。
- [x] 4.3 提供许可到期、日志容量、节点阈值的后台提醒任务入口。

## 5. UI alignment and verification

- [x] 5.1 许可列表卡片、默认提醒面板、添加许可弹窗和许可提醒弹窗按当前原型结构收敛实现。
- [x] 5.2 许可提醒相关弹窗统一使用 `OperateModal`。
- [x] 5.3 执行 OpenSpec 状态检查，确认变更目录可被 spec-driven 流程识别。
- [ ] 5.4 执行 `cd web && pnpm lint && pnpm type-check`，确认当前前端实现通过最小门禁。
