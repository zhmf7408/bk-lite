## 1. 类型定义扩展

- [x] 1.1 在 `web/src/app/ops-analysis/types/dashBoard.ts` 中定义 `DashboardFilters`、`UnifiedFilterDefinition`、`FilterValue`、`TimeRangeValue` 类型
- [x] 1.2 在 `web/src/app/ops-analysis/types/dashBoard.ts` 中扩展 `ValueConfig` 接口，添加 `filterBindings?: FilterBindings` 字段
- [x] 1.3 在 `web/src/app/ops-analysis/types/dashBoard.ts` 中定义 `FilterBindings`、`ScannedFilterParam`、`BindingValidationResult` 类型

## 2. 状态管理 Hook

- [x] 2.1 创建 `web/src/app/ops-analysis/hooks/useUnifiedFilter.ts`
- [x] 2.2 实现 `filterValues` 状态管理和 `setFilterValues` 方法
- [x] 2.3 实现 `updateDefinitions` 方法更新筛选项定义
- [x] 2.4 实现 `getEffectiveParams` 方法按优先级合并参数
- [x] 2.5 实现 `validateBindings` 方法校验绑定有效性

## 3. 参数合并逻辑

- [x] 3.1 修改 `web/src/app/ops-analysis/utils/widgetDataTransform.ts` 中的 `processDataSourceParams` 函数
- [x] 3.2 添加统一筛选值注入逻辑，遵循优先级：fixed > 统一筛选 > params > 默认值
- [x] 3.3 处理统一筛选无值时不传参数的逻辑

## 4. 统一筛选栏组件

- [x] 4.1 创建 `web/src/app/ops-analysis/components/unifiedFilter/` 目录
- [x] 4.2 实现 `UnifiedFilterBar.tsx` 组件，按 order 渲染筛选控件
- [x] 4.3 实现 string 类型筛选控件（Input）
- [x] 4.4 实现 timeRange 类型筛选控件（DateRangePicker）
- [x] 4.5 实现编辑态显示配置按钮、查看态隐藏的逻辑
- [x] 4.6 实现空状态时不显示筛选栏的逻辑

## 5. 统一筛选配置弹窗

- [x] 5.1 实现 `UnifiedFilterConfigModal.tsx` 组件
- [x] 5.2 实现参数自动扫描逻辑（收集 filterType='filter' 且 type 为 string/timeRange 的参数）
- [x] 5.3 实现按 key + type 联合去重逻辑
- [x] 5.4 实现可选参数列表展示（参数 key、类型、匹配组件数、默认显示名）
- [x] 5.5 实现筛选项添加功能
- [x] 5.6 实现筛选项编辑功能（修改显示名称、默认值、顺序、启用状态）
- [x] 5.7 实现筛选项删除功能
- [x] 5.8 实现筛选项拖拽排序功能

## 6. 组件绑定配置面板

- [x] 6.1 实现 `FilterBindingPanel.tsx` 组件
- [x] 6.2 实现自动匹配 key + type 的逻辑
- [x] 6.3 实现绑定开关（匹配时可启用）
- [x] 6.4 实现禁用状态展示（不匹配时显示原因：类型不匹配 / 组件无此参数）

## 7. 仪表盘集成

- [x] 7.1 在 `web/src/app/ops-analysis/(pages)/view/dashBoard/index.tsx` 中集成 `useUnifiedFilter` hook
- [x] 7.2 在仪表盘顶部集成 `UnifiedFilterBar` 组件
- [x] 7.3 实现筛选值变更时触发组件刷新的逻辑
- [x] 7.4 将 filters 配置纳入仪表盘保存逻辑

## 8. 组件配置抽屉集成

- [x] 8.1 在 `web/src/app/ops-analysis/(pages)/view/dashBoard/components/viewConfig.tsx` 中添加"统一筛选绑定"区域
- [x] 8.2 集成 `FilterBindingPanel` 组件
- [x] 8.3 将 filterBindings 纳入组件配置保存逻辑

## 9. 绑定失效警告

- [x] 9.1 在 `web/src/app/ops-analysis/(pages)/view/dashBoard/components/widgetWrapper.tsx` 中添加失效检测逻辑
- [x] 9.2 实现警告图标渲染（组件右上角）
- [x] 9.3 实现 Hover Tooltip 显示失效原因

## 10. 后端 YAML 导入导出

- [x] 10.1 修改 `server/apps/operation_analysis/schemas/import_export_schema.py`，在 dashboard schema 中添加 filters 字段
- [x] 10.2 在 view_sets 的 valueConfig 中添加 filterBindings 字段
- [x] 10.3 验证导出时 filters.values 为空对象

## 11. 测试与验证

- [x] 11.1 执行 `cd web && pnpm lint && pnpm type-check` 确保类型检查通过
- [ ] 11.2 手动验证：定义统一筛选项并保存，刷新后回显正确
- [ ] 11.3 手动验证：组件绑定后，修改统一筛选值，组件正确刷新
- [ ] 11.4 手动验证：数据源参数变更导致绑定失效，警告图标正确显示
- [ ] 11.5 手动验证：YAML 导出包含 filters 配置，导入后恢复正确
- [ ] 11.6 回归验证：现有仪表盘无统一筛选时功能不受影响
