## Why

运营分析仪表盘当前缺乏统一筛选能力，用户需要逐个配置每个组件的筛选参数（如时间范围、环境、命名空间），操作繁琐且容易遗漏。需要在仪表盘层面提供统一筛选功能，让多个组件可以共享筛选条件，一次修改、全局生效。

## What Changes

- 新增仪表盘顶部统一筛选栏，支持「关键字输入」和「时间范围」两种控件类型
- 自动扫描画布组件，收集 `filterType='filter'` 的参数供用户选择
- 组件级显式绑定：用户通过开关控制是否将组件参数绑定到统一筛选
- 绑定规则：仅当参数 key 和 type 都匹配时才可绑定
- 统一筛选值变更时，所有已绑定组件自动重新请求数据
- 绑定失效时，组件右上角显示警告图标提示用户
- **BREAKING**: 时间类型筛选不再使用 `other.timeSelector`，统一存入 `Dashboard.filters`

## Capabilities

### New Capabilities

- `dashboard-unified-filter`: 仪表盘统一筛选功能，包括筛选项定义、组件绑定、值变更联动、失效检测

### Modified Capabilities

<!-- 无需修改现有 spec，数据源参数分类机制(filterType)已存在 -->

## Impact

- **前端**:
  - `web/src/app/ops-analysis/types/dashBoard.ts` - 扩展 Dashboard.filters 类型
  - `web/src/app/ops-analysis/utils/widgetDataTransform.ts` - 参数合并逻辑支持统一筛选
  - `web/src/app/ops-analysis/(pages)/view/dashBoard/` - 集成筛选栏和配置
  - 新增 `unifiedFilter/` 组件目录和 `useUnifiedFilter` hook

- **后端**:
  - `server/apps/operation_analysis/schemas/import_export_schema.py` - YAML 导入导出支持 filters

- **数据存储**:
  - 复用现有 `Dashboard.filters` JSONField，无需数据库迁移
