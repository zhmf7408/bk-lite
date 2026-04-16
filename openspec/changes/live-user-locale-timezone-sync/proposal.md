## Why

用户在个人信息抽屉中修改语言和时区后，当前页面不会立即切换，通常要依赖重新登录或完整刷新才能看到变化。这会造成偏好设置已保存但运行态仍使用旧值，导致页面文案、Ant Design 组件语言、前端时间展示以及后端按用户时区返回的数据彼此不一致。

## What Changes

- 为用户语言与时区引入统一的运行时偏好同步机制，使保存后当前页面文案与时间立即切换。
- 扩展当前认证会话载荷，确保 locale 与 timezone 在保存后可被前端上下文和后续请求立即消费，而不需要重新登录。
- 统一前端语言和时间相关消费者的取值来源，覆盖 React 国际化文案、Ant Design locale、dayjs locale 以及依赖用户时区的时间格式化逻辑。
- 明确后端请求上下文中的用户时区生效路径，并补齐关键接口的时间序列化，使接口返回按最新用户时区输出。

## Capabilities

### New Capabilities
- `user-preference-runtime-sync`: 定义用户修改语言和时区后，当前前端运行态、认证会话和后端时间返回必须立即同步生效的行为。

### Modified Capabilities

## Impact

- Web 前端认证与运行时上下文：next-auth session、LocaleProvider、ThemeProvider、用户信息抽屉、时间格式化 hooks。
- Server 用户偏好读取与时间序列化：用户基础信息更新接口、基于 token 的用户信息装载、依赖用户时区的接口输出。
- 相关系统：用户偏好持久化、认证态同步、国际化文案加载、时间展示与时间字段接口返回。