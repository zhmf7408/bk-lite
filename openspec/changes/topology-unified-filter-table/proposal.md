## Why

拓扑图当前缺乏与仪表盘一致的统一筛选能力。用户在拓扑图中添加图表/单值节点后，无法像仪表盘那样通过顶部筛选栏统一控制多个节点的筛选条件。此外，拓扑图还缺少：
- 表格类型节点支持
- 取消编辑按钮（恢复到进入编辑模式时的状态）
- 筛选配置入口

需要将仪表盘的统一筛选能力复用到拓扑图，保持两个视图的交互一致性。

## What Changes

- 新增拓扑图顶部统一筛选栏，复用仪表盘的 `UnifiedFilterBar` 组件
- 新增命名空间选择器，从 chart/single-value/table 节点提取可用命名空间
- 新增筛选配置按钮（编辑模式下显示），复用 `UnifiedFilterConfigModal`
- 新增取消编辑按钮，恢复到进入编辑模式时的图状态
- 新增表格类型节点（table），复用仪表盘的 `ComTable` 组件
- 扩展节点 `valueConfig` 支持 `filterBindings` 和 `tableConfig`
- 点击搜索时刷新所有关联了筛选项的 chart/single-value/table 节点
- 拓扑图保存/加载时包含 `filters` 字段

## Capabilities

### New Capabilities

- `topology-unified-filter`: 拓扑图统一筛选功能，复用仪表盘筛选组件
- `topology-table-node`: 拓扑图表格节点支持

### Modified Capabilities

- `topology-edit-mode`: 新增取消编辑功能，恢复到进入编辑模式时的状态

## Impact

- **前端**:
  - `web/src/app/ops-analysis/(pages)/view/topology/index.tsx` - 集成筛选栏、筛选配置、取消按钮
  - `web/src/app/ops-analysis/(pages)/view/topology/components/toolbar.tsx` - 添加筛选配置和取消按钮
  - `web/src/app/ops-analysis/(pages)/view/topology/components/tableNode.tsx` - 新增表格节点组件
  - `web/src/app/ops-analysis/(pages)/view/topology/components/chartNode.tsx` - 扩展支持 table 类型
  - `web/src/app/ops-analysis/(pages)/view/topology/components/nodeSidebar.tsx` - 添加表格节点拖拽选项
  - `web/src/app/ops-analysis/(pages)/view/topology/hooks/useGraphData.ts` - 保存/加载 filters
  - `web/src/app/ops-analysis/(pages)/view/topology/hooks/useGraphOperations.ts` - 筛选刷新逻辑
  - `web/src/app/ops-analysis/(pages)/view/topology/utils/registerNode.ts` - 注册 table 节点
  - `web/src/app/ops-analysis/types/topology.ts` - 扩展类型定义

- **复用组件**（无需修改）:
  - `web/src/app/ops-analysis/components/unifiedFilter/` - 筛选栏和配置弹窗
  - `web/src/app/ops-analysis/(pages)/view/dashBoard/widgets/comTable.tsx` - 表格组件
  - `web/src/app/ops-analysis/(pages)/view/dashBoard/components/viewConfig.tsx` - 已在拓扑图中使用

- **数据存储**:
  - 拓扑图 `view_sets` 结构扩展，添加 `filters` 字段
