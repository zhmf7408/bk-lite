## Why

Redis Tool Editor 编辑弹窗存在三个交互缺陷：

1. `OperateModal` 未设置 `width`，使用 Ant Design 默认 520px，而 `RedisToolEditor` 左侧列表固定 `w-[260px]`，导致右侧表单区域仅剩约 220px，字段过于拥挤、难以操作。
2. `handleAddRedisInstance` 在 `setRedisInstances` 的 state updater 回调内部调用 `setSelectedRedisInstanceId`，触发时 instances 状态尚未更新，`RedisToolEditor` 找不到对应 ID，右侧表单渲染为空白。
3. 新增实例后列表不会自动滚动到底部，用户需要手动向下滚动才能看到刚添加的条目。

## What Changes

- 为编辑 Redis 工具的 `OperateModal` 设置合适的宽度，使左侧列表与右侧表单都有充足空间。
- 将 `setSelectedRedisInstanceId` 调用从 `setRedisInstances` updater 内部移至外部，确保新实例被添加到状态后才设置选中 ID，消除空白渲染问题。
- 在 `RedisToolEditor` 左侧列表中增加自动滚动逻辑，新增实例后自动定位到最后一个条目。

## Capabilities

### New Capabilities

### Modified Capabilities
- `redis-tool-editor-interaction`: 修复 Redis Tool Editor 编辑弹窗的宽度、新增空白与自动滚动交互缺陷。

## Impact
