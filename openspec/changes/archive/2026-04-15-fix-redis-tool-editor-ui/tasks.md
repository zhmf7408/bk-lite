## 1. 修复弹窗宽度

- [x] 1.1 在 `web/src/app/opspilot/components/skill/toolSelector.tsx` 中，找到 Redis 编辑场景使用的 `OperateModal`，为其添加 `width={800}` prop。

## 2. 修复新增后空白问题

- [x] 2.1 在 `toolSelector.tsx` 的 `handleAddRedisInstance` 中，将新实例的创建移出 `setRedisInstances` updater，分别独立调用 `setRedisInstances` 与 `setSelectedRedisInstanceId`。

## 3. 新增后自动滚动到最后一个条目

- [x] 3.1 在 `web/src/app/opspilot/components/skill/redisToolEditor.tsx` 中，为左侧列表的 `overflow-y-auto` div 添加 `ref`，并通过 `useEffect` 监听 `instances.length` 变化，在长度增大时将 `scrollTop` 设为 `scrollHeight`。

## 4. 验证

- [x] 4.1 执行 `cd web && pnpm type-check` 确认无类型错误。
