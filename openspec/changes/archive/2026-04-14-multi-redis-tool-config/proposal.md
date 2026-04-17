## Why

当前 OpsPilot 内置 Redis 工具的配置协议只支持一套扁平连接参数，例如 `url`、`username`、`password`、`cluster_mode`。虽然一个智能体可以挂多个工具，但 Redis 工具运行时最终只会读取这一套固定键，因此同一个智能体无法稳定管理多个 Redis 实例。

用户期望在智能体配置中直接维护多个 Redis 实例：左侧展示实例列表，可新增/删除；每个实例拥有独立名称和连接参数；可单独执行“测试连接”，并在右上角看到未测试/成功/失败状态。这一需求不仅是表单增强，还要求 Redis 工具的持久化结构与执行时取参方式升级为多实例协议。

## What Changes

- 将内置 Redis 工具的配置从“单实例扁平参数”升级为“多实例列表 + 默认实例”。
- 为 Redis 工具提供实例级配置 UI，支持新增、删除、编辑 Redis 实例，并为实例名称提供默认命名规则 `Redis - n`。
- 为每个 Redis 实例增加独立的测试连接能力和状态展示：未测试、测试成功、测试失败。
- 调整 Redis 工具运行时配置契约，使其读取 `redis_instances` 与 `redis_default_instance_id`，而不是直接依赖单套 `url` 等字段。
- 为 Redis 子工具增加实例选择能力：未显式指定时使用默认实例，显式指定时切换到对应实例执行。

## Capabilities

### New Capabilities
- `redis-tool-multi-instance`: 定义单个智能体内的 Redis 工具可配置并使用多个 Redis 实例。

### Modified Capabilities
- `redis-tool-multi-instance`: Redis 工具的前端编辑方式、持久化数据结构、测试连接行为与运行时连接解析整体更新。

## Impact

- Web OpsPilot 智能体配置：工具选择器、Redis 工具编辑弹窗、实例级测试状态与交互文案。
- Server OpsPilot 工具执行链路：技能工具参数持久化、Redis 连接配置解析、Redis 工具调用时的实例选择。
- Redis 内置工具集：连接构造函数、工具描述提示、实例切换与测试连接接口。
