## Why

系统管理已经落地许可管理能力，但 `openspec/changes/license-mgmt` 仍停留在早期规划文档形态，未转换为当前仓库使用的 spec-driven 变更结构，导致 OpenSpec 无法识别该变更已经实现完成，也无法进入归档流程。

## What Changes

- 将 `license-mgmt` 变更整理为当前仓库可识别的 spec-driven 结构，补齐 `proposal.md`、`design.md`、`specs/**` 与可解析的 `tasks.md`。
- 以当前实际实现为准，明确许可管理已经覆盖的能力范围：企业版许可页入口、许可列表与历史许可、注册码读取与许可导入、默认/单许可/节点/日志提醒、许可剩余时间状态展示、资源新增许可拦截。
- 将前端提醒面板与许可提醒弹窗内容区继续收敛到原型结构，统一使用现有 `OperateModal` 与原型样式语义。

## Capabilities

### New Capabilities

- `license-management-page`: 系统管理设置中的企业版许可管理页面，包含许可列表、默认提醒、历史许可、平台模块与提醒配置交互。
- `license-reminder-governance`: 全局提醒、单许可提醒、节点提醒与日志容量提醒的统一配置与回显能力。
- `license-create-guard`: 基于 `LICENSE_APP_PERMISSIONS` 与 RPC 校验的新增资源许可拦截能力。

### Modified Capabilities

- `license-management-page`: 许可卡片状态与提醒配置内容区改为按当前提醒状态和原型结构展示。

## Impact

- **Web 前端**
  - `web/src/app/system-manager/(pages)/settings/license/page.tsx`
  - `web/src/app/system-manager/enterprise/(pages)/settings/license/page.tsx`
  - `web/src/app/system-manager/enterprise/api/license_mgmt/index.ts`
- **Server 后端**
  - `server/apps/license_mgmt/services/license_service.py`
  - `server/apps/license_mgmt/services/reminder_service.py`
  - `server/apps/license_mgmt/services/license_decode_service.py`
  - `server/apps/license_mgmt/middleware/license_guard.py`
  - `server/apps/license_mgmt/tasks.py`
- **OpenSpec artifacts**
  - `openspec/changes/license-mgmt/design.md`
  - `openspec/changes/license-mgmt/specs/license-management/spec.md`
  - `openspec/changes/license-mgmt/tasks.md`
