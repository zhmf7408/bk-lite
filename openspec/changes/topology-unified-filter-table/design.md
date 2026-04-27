## Context

拓扑图已具备以下基础设施：
- X6 图形引擎，支持节点拖拽、连线、缩放等操作
- `chart` 和 `single-value` 节点类型，通过 `valueConfig` 配置数据源
- `ViewConfig` 组件用于配置图表节点（已复用仪表盘组件）
- `useGraphData` hook 处理拓扑图的保存/加载
- `useGraphOperations` hook 处理图形操作和节点数据刷新

仪表盘已实现的统一筛选功能：
- `UnifiedFilterBar` 组件渲染筛选栏
- `UnifiedFilterConfigModal` 组件配置筛选项
- `useUnifiedFilter` hook 管理筛选状态
- `collectNamespaceOptions` 从组件提取命名空间选项
- `buildFiltersFromLayout` 从组件构建筛选定义

本设计复用仪表盘组件，最小化新增代码。

## Goals / Non-Goals

**Goals:**
- 拓扑图顶部显示统一筛选栏，与仪表盘交互一致
- 命名空间选择器从 chart/single-value/table 节点提取选项
- 编辑模式下显示筛选配置按钮，打开配置弹窗
- 编辑模式下显示取消按钮，恢复到进入编辑模式时的状态
- 新增表格节点类型，复用 `ComTable` 组件
- 点击搜索时刷新所有关联节点
- 拓扑图保存/加载包含 filters 配置

**Non-Goals:**
- 不实现拓扑图专属的筛选控件类型（复用仪表盘的 string/timeRange）
- 不实现节点显示/隐藏联动（仅刷新数据）
- 不实现跨拓扑图共享筛选状态
- 不修改后端 API（复用现有 topology API）

## Decisions

### D1: 筛选栏位置

**决策**: 筛选栏放在工具栏下方、画布上方，与仪表盘布局一致

**理由**:
- 保持两个视图的交互一致性
- 筛选栏不占用画布空间，不影响节点拖拽

### D2: 命名空间选项提取

**决策**: 从 X6 Graph 节点提取，适配 `collectNamespaceOptions` 函数

**理由**:
- 拓扑图节点结构与仪表盘 LayoutItem 不同，需要适配
- 仅从 chart/single-value/table 节点提取，其他节点（icon/text/basic-shape）不参与

**实现**:
```typescript
const collectNamespaceOptionsFromNodes = (
  graphInstance: Graph,
  dataSources: DatasourceItem[],
  namespaceList: Array<{ id: number; name: string }>
): NamespaceOption[] => {
  const namespaceIds = new Set<number>();
  
  graphInstance.getNodes().forEach(node => {
    const nodeData = node.getData();
    if (['chart', 'single-value', 'table'].includes(nodeData.type)) {
      const dsId = nodeData.valueConfig?.dataSource;
      const ds = dataSources.find(d => d.id === dsId);
      if (ds?.namespaces) {
        ds.namespaces.forEach(id => namespaceIds.add(id));
      }
    }
  });
  
  return namespaceList
    .filter(ns => namespaceIds.has(ns.id))
    .map(ns => ({ label: ns.name, value: ns.id }));
};
```

### D3: 取消编辑的状态恢复

**决策**: 进入编辑模式时保存完整图状态（`graphInstance.toJSON()`），取消时恢复

**理由**:
- X6 提供 `toJSON()` / `fromJSON()` 方法，可完整保存/恢复图状态
- 包括节点位置、连线、数据等所有信息

**风险**:
- `rawData`（图表数据）可能不在 JSON 中，需要重新加载
- Mitigation: 恢复后触发一次全量刷新

### D4: 筛选刷新机制

**决策**: 点击搜索时遍历所有节点，根据 `filterBindings` 判断是否需要刷新

**理由**:
- 与仪表盘的 `searchKey` 机制不同，拓扑图节点是 X6 React 节点
- 需要主动调用 `loadChartNodeData` / `updateSingleNodeData` 刷新数据

**实现**:
```typescript
const refreshFilteredNodes = (filterValues: Record<string, FilterValue>) => {
  graphInstance.getNodes().forEach(node => {
    const nodeData = node.getData();
    if (!['chart', 'single-value', 'table'].includes(nodeData.type)) return;
    
    const bindings = nodeData.valueConfig?.filterBindings;
    if (!bindings || !hasActiveBindings(bindings, filterValues)) return;
    
    if (nodeData.type === 'chart' || nodeData.type === 'table') {
      loadChartNodeData(node.id, nodeData.valueConfig, filterValues);
    } else if (nodeData.type === 'single-value') {
      updateSingleNodeData(nodeData, filterValues);
    }
  });
};
```

### D5: 表格节点实现

**决策**: 创建 `tableNode.tsx`，复用 `ComTable` 组件，与 `chartNode.tsx` 结构类似

**理由**:
- 表格组件已在仪表盘中实现，直接复用
- 表格节点需要处理分页、筛选等内部状态

**注意**:
- 表格节点默认尺寸需要比图表节点大（建议 400x300）
- 表格内部筛选与统一筛选独立，不冲突

### D6: 数据持久化

**决策**: 拓扑图保存数据结构扩展为 `{ name, view_sets: { nodes, edges }, filters }`

**理由**:
- 与仪表盘结构对齐
- `filters` 存储 `UnifiedFilterDefinition[]`

## Risks / Trade-offs

**[Risk] X6 状态恢复不完整** → `toJSON()` 可能不包含 React 节点的运行时数据
- Mitigation: 恢复后触发全量刷新；测试验证恢复完整性

**[Risk] 表格节点性能** → 大数据量表格在拓扑图中渲染可能卡顿
- Mitigation: 表格默认分页 20 条；用户可调整节点大小

**[Trade-off] 复用 vs 定制**
- 选择最大化复用仪表盘组件，减少代码量
- 代价：拓扑图特有需求可能需要后续扩展
