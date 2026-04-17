## Why

当前系统管理中的“设置 / 门户”直接实现在社区版模块内，导致社区版和商业版在同一套菜单、页面和构建入口上耦合。随着后续还会有更多“社区版不展示、商业版追加”的能力，如果不先把门户抽成一层 enterprise overlay，双仓开发和后续维护都会持续放大冲突成本。

## What Changes

- 将系统管理中的“门户”从社区版默认菜单中移除，社区版保留稳定路由入口但不默认展示该能力。
- 在仓库根目录新增 `enterprise/` 扩展层，并按 `enterprise/web`、`enterprise/server` 分离商业版前后端增量实现。
- 为系统管理菜单引入 enterprise patch 注入方式，使商业版可以在不改写社区版基础菜单文件的前提下，将“门户”菜单追加到“设置”下。
- 将 `/system-manager/settings/portal` 调整为稳定的 overlay 入口页：有 enterprise 实现时加载商业版页面，没有实现时回退到受控 stub。
- 保持现有门户配置读写接口和页面 URL 不变，避免商业版功能抽离后影响已有数据和访问路径。

## Capabilities

### New Capabilities
- `portal-enterprise-overlay`: 定义系统管理门户能力如何从社区版主干中抽离，并通过 enterprise overlay 方式注入菜单和页面实现。

### Modified Capabilities

## Impact

- **Web 前端**:
  - `web/src/app/system-manager/constants/menu.json`
  - `web/src/app/system-manager/(pages)/settings/portal/page.tsx`
  - `web/src/app/(core)/api/menu/route.ts` 消费 enterprise 菜单 patch
  - `web/tsconfig.json`、`web/tsconfig.lint.json`、`web/src/lib/enterpriseStub.ts`
  - 新增 `enterprise/web/src/app/system-manager/` 作为商业版页面与菜单 patch 目录
- **构建与装配**:
  - 使用现有 `NEXTAPI_INSTALL_APP` 扫描机制，将根目录 `enterprise/web` 下的菜单来源接入社区版构建
- **后端/数据**:
  - 复用现有 portal settings 接口与配置项，无需新增数据库迁移
  - 预留 `enterprise/server` 作为后续商业版后端扩展目录
