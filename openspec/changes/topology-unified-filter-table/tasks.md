## 1. 类型定义扩展

- [x] 1.1 在 `web/src/app/ops-analysis/types/topology.ts` 中扩展 `TopologyValueConfig`，添加 `filterBindings?: FilterBindings` 和 `tableConfig?: TableConfig` 字段
- [x] 1.2 在 `web/src/app/ops-analysis/types/topology.ts` 中扩展 `TopologySaveData`，添加 `filters?: UnifiedFilterDefinition[]` 字段

## 2. 工具栏改造

- [x] 2.1 修改 `web/src/app/ops-analysis/(pages)/view/topology/components/toolbar.tsx`，添加 `onCancel` 和 `onFilterConfig` props
- [x] 2.2 在编辑模式下添加「筛选配置」按钮，点击触发 `onFilterConfig`
- [x] 2.3 在编辑模式下添加「取消」按钮，点击触发 `onCancel`，按钮位置在保存按钮左侧

## 3. 主组件集成筛选栏

- [x] 3.1 在 `web/src/app/ops-analysis/(pages)/view/topology/index.tsx` 中添加筛选相关状态：`definitions`, `filterValues`, `originalDefinitions`, `searchKey`, `selectedNamespaceId`
- [x] 3.2 添加 `originalGraphState` 状态，用于取消编辑时恢复
- [x] 3.3 在工具栏下方、画布上方集成 `UnifiedFilterBar` 组件
- [x] 3.4 集成 `UnifiedFilterConfigModal` 组件
- [x] 3.5 实现 `handleCancelEdit` 函数，恢复图状态和筛选定义
- [x] 3.6 实现 `handleFilterConfigConfirm` 函数，更新筛选定义

## 4. 命名空间选项提取

- [x] 4.1 创建 `collectNamespaceOptionsFromNodes` 函数，从 X6 节点提取命名空间选项
- [x] 4.2 在主组件中使用 `useMemo` 计算命名空间选项
- [x] 4.3 实现命名空间选择器，选择变化时触发节点刷新

## 5. 筛选刷新逻辑

- [x] 5.1 使用 `searchKey` 状态触发筛选刷新（与仪表盘一致）
- [x] 5.2 命名空间选择变化时递增 `searchKey` 触发刷新
- [x] 5.3 筛选值变化时递增 `searchKey` 触发刷新
- [x] 5.4 筛选配置确认时递增 `searchKey` 触发刷新

## 6. 取消编辑功能

- [x] 6.1 在进入编辑模式时保存 `graphInstance.toJSON()` 到 `originalGraphState`
- [x] 6.2 在进入编辑模式时保存 `definitions` 到 `originalDefinitions`
- [x] 6.3 实现取消编辑时恢复图状态：`graphInstance.fromJSON(originalGraphState)`
- [x] 6.4 实现取消编辑时恢复筛选定义：`setDefinitions([...originalDefinitions])`
- [x] 6.5 恢复后触发全量节点刷新

## 7. 表格节点支持

- [x] 7.1 表格作为图表类型，无需单独创建 tableNode.tsx
- [x] 7.2 表格作为图表类型，无需单独注册节点
- [x] 7.3 表格作为图表类型，通过 ViewConfig 选择 chartType=table
- [x] 7.4 在 `chartNode.tsx` 的 `componentMap` 中添加 `table: ComTable`
- [x] 7.5 表格使用 CHART_NODE 默认尺寸 400x220

## 8. 数据持久化

- [x] 8.1 修改 `useGraphData.ts` 中的 `handleSaveTopology`，保存时包含 `filters` 字段
- [x] 8.2 修改 `useGraphData.ts` 中的 `handleLoadTopology`，加载时读取 `filters` 字段并返回
- [x] 8.3 在主组件加载拓扑时设置 `definitions` 和 `originalDefinitions`

## 9. 筛选定义构建

- [x] 9.1 创建 `buildFiltersFromNodes` 函数，从 X6 节点构建筛选定义（类似仪表盘的 `buildFiltersFromLayout`）
- [x] 9.2 创建 `convertNodesToLayoutItems` 函数，用于 UnifiedFilterConfigModal
- [x] 9.3 筛选定义通过 UnifiedFilterConfigModal 手动配置

## 10. ViewConfig 集成

- [x] 10.1 确认 `ViewConfig` 组件已支持 `filterBindings` 配置（仪表盘已实现）
- [x] 10.2 确认 `ViewConfig` 组件已支持 `tableConfig` 配置（仪表盘已实现）
- [x] 10.3 在拓扑图中传递 `filterDefinitions` 给 `ViewConfig`

## 11. 测试与验证

- [x] 11.1 执行 `cd web && pnpm lint && pnpm type-check` 确保类型检查通过
- [ ] 11.2 手动验证：拓扑图添加图表节点，筛选栏正确显示
- [ ] 11.3 手动验证：配置筛选项并保存，刷新后回显正确
- [ ] 11.4 手动验证：点击搜索，关联节点正确刷新
- [ ] 11.5 手动验证：取消编辑，图状态正确恢复
- [ ] 11.6 手动验证：添加表格节点，数据正确显示
- [ ] 11.7 手动验证：命名空间选择器正确过滤节点数据
