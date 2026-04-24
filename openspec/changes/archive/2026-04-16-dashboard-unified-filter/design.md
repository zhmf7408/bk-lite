## Context

运营分析仪表盘已具备以下基础设施：
- `ParamItem.filterType` 字段支持 `'fixed' | 'filter' | 'params'` 三种参数分类
- `Dashboard.filters` JSONField 已预留（当前为空 `{}`）
- `processDataSourceParams()` 函数处理参数优先级和合并逻辑
- 时间范围通过 `globalTimeRange` 传递给组件（仅限 `type='timeRange'`）

本设计在现有架构上扩展，复用已有字段和函数，最小化改动范围。

## Goals / Non-Goals

**Goals:**
- 仪表盘级定义统一筛选项，支持 `string` 和 `timeRange` 两种控件类型
- 自动扫描画布组件收集可筛选参数，按 key + type 联合去重
- 组件级显式绑定（开关控制），绑定规则为 key + type 都匹配
- 统一筛选值变更时联动刷新所有已绑定组件
- 绑定失效时显示警告图标
- YAML 导入导出支持 filters 字段

**Non-Goals:**
- 不实现单选下拉控件（本期仅 string 和 timeRange）
- 不兼容旧数据的 `other.timeSelector` 字段
- 不实现跨仪表盘共享筛选状态
- 不实现图表点击联动、钻取联动
- 不实现统一筛选必填配置

## Decisions

### D1: 数据结构设计

**决策**: `Dashboard.filters` 存储 `{ definitions, values }`，组件绑定存储在 `LayoutItem.valueConfig.filterBindings`

**理由**: 
- 筛选定义是仪表盘级别，值是运行时状态，两者分离便于管理
- 绑定关系属于组件配置，存在 valueConfig 符合现有数据组织方式
- 不引入新的顶层字段，减少 schema 变更

**备选方案**:
- A. 所有配置集中在 Dashboard.filters → 组件需要反向查询，耦合度高
- B. 新增独立的 filterBindings 顶层字段 → 增加 schema 复杂度

### D2: 参数优先级

**决策**: `固定参数 > 统一筛选 > 组件私有参数 > 数据源默认值`

**理由**:
- 固定参数（filterType='fixed'）是数据源强制配置，不应被覆盖
- 统一筛选是仪表盘级意图，优先于组件私有配置
- 组件私有参数作为兜底，保持向后兼容

### D3: 绑定匹配规则

**决策**: 仅当参数 `key`（name 字段）和 `type` 都匹配时才可绑定

**理由**:
- key 相同但 type 不同（如 env 既有 string 又有 number）是不同参数
- 类型不匹配会导致运行时错误（如把字符串传给时间控件）

### D4: 失效检测时机

**决策**: 每次加载仪表盘时实时校验绑定有效性

**理由**:
- 数据源可能被修改（参数增删改），需要实时校验
- 不在保存时校验，避免阻塞用户操作

### D5: 无值处理

**决策**: 统一筛选无值时，不传该筛选参数

**理由**:
- 让后端按默认逻辑处理，避免传空值导致的边界问题
- 与现有参数处理行为一致

## Risks / Trade-offs

**[Risk] 扫描性能** → 画布组件数量大时扫描耗时
- Mitigation: 扫描仅在打开配置弹窗时执行，非热路径；组件数量通常 < 50

**[Risk] 绑定失效累积** → 用户不处理警告导致大量失效绑定
- Mitigation: 失效绑定不影响组件正常工作（使用默认值）；警告图标提供清晰入口

**[Risk] BREAKING 时间类型迁移** → 旧仪表盘使用 other.timeSelector
- Mitigation: 本期不兼容旧数据，需用户重新配置；影响范围可控（运营分析模块内部）

**[Trade-off] 显式绑定 vs 自动绑定**
- 选择显式绑定：用户控制更精细，避免意外联动
- 代价：配置步骤多一步（开关确认）
