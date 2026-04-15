## Context

`RedisToolEditor` 是一个左右分栏布局的组件：左侧为固定宽度 `w-[260px]` 的实例列表，右侧为 `flex-1` 的配置表单。该组件被包裹在 `OperateModal` 中展示。当前 `OperateModal` 没有传入 `width`，使用 Ant Design 默认 520px，导致右侧空间严重不足。

新增实例的逻辑位于 `toolSelector.tsx` 的 `handleAddRedisInstance`，当前在 `setRedisInstances` updater 内部调用 `setSelectedRedisInstanceId`，违反 React state updater 应为纯函数的原则，并导致选中 ID 在 instances 更新前已被设置，右侧表单找不到对应实例而显示空状态。

## Goals / Non-Goals

**Goals:**
- 弹窗宽度足以容纳左右分栏布局，右侧表单字段有正常的可用空间。
- 点击"添加"后右侧立即展示新实例的配置表单，不出现空白。
- 新增实例后，左侧列表自动滚动到最后一个条目可见。

**Non-Goals:**
- 不改动 Redis Tool Editor 的功能逻辑或表单字段。
- 不修改 `OperateModal` 的全局默认宽度，仅在 Redis 编辑场景透传宽度。
- 不引入新的动画或过渡效果。

## Decisions

### 1. 将 `width={800}` 通过 `OperateModal` props 传入

`OperateModal` 已通过 `...modalProps` 将所有额外 props 透传给 Ant Design `Modal`，因此只需在 `toolSelector.tsx` 中对 Redis 编辑弹窗加 `width={800}`，不需要改动 `OperateModal` 组件本身。

选择原因：最小改动，不影响其他使用 `OperateModal` 的场景。800px 在左侧 260px + padding 后，右侧约 480px，满足表单展示需求。

### 2. 将 `setSelectedRedisInstanceId` 移出 state updater

在 `handleAddRedisInstance` 中，先用当前 `redisInstances` 计算新实例，再分别调用 `setRedisInstances` 和 `setSelectedRedisInstanceId`，React 会在同一批次内应用两次状态更新，确保渲染时两个状态同步。

```ts
// Before (buggy)
const handleAddRedisInstance = () => {
  setRedisInstances((prev) => {
    const nextInstance = getDefaultRedisInstance(getNextRedisInstanceName(prev));
    setSelectedRedisInstanceId(nextInstance.id); // ❌ side effect in updater
    return [...prev, nextInstance];
  });
};

// After (correct)
const handleAddRedisInstance = () => {
  const nextInstance = getDefaultRedisInstance(getNextRedisInstanceName(redisInstances));
  setRedisInstances((prev) => [...prev, nextInstance]);
  setSelectedRedisInstanceId(nextInstance.id);
};
```

### 3. 在 `RedisToolEditor` 列表容器上挂载 `useRef`，通过 `useEffect` 在 instances 长度变化时滚动到底部

`redisToolEditor.tsx` 接受 `instances` 作为 prop，当 `instances.length` 增大时，说明刚刚新增了条目，此时对列表容器调用 `scrollTop = scrollHeight` 即可滚到底部。

```ts
const listRef = useRef<HTMLDivElement>(null);
const prevLengthRef = useRef(instances.length);

useEffect(() => {
  if (instances.length > prevLengthRef.current && listRef.current) {
    listRef.current.scrollTop = listRef.current.scrollHeight;
  }
  prevLengthRef.current = instances.length;
}, [instances.length]);
```

挂载到现有的 `overflow-y-auto` 列表 div 上，不新增任何 DOM 元素。
