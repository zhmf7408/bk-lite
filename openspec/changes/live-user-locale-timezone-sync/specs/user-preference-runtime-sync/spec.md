## ADDED Requirements

### Requirement: 保存用户偏好后当前页面必须立即切换语言与时间
当已认证用户在个人信息设置中保存新的 locale 和 timezone 后，系统 MUST 在当前页面立即应用新的语言和时区，而不要求用户重新登录。

#### Scenario: 当前页面文案立即切换
- **WHEN** 用户保存新的 locale 且保存请求成功
- **THEN** 当前页面的 React 国际化文案和 Ant Design 组件语言 MUST 切换为新的 locale

#### Scenario: 当前页面时间立即切换
- **WHEN** 用户保存新的 timezone 且当前页面存在依赖用户时区显示的时间内容
- **THEN** 当前页面已渲染的相关时间内容 MUST 按新的 timezone 重新计算并显示

### Requirement: 认证会话必须同步最新的 locale 和 timezone
系统 MUST 在用户偏好保存成功后，使当前认证会话携带最新的 locale 和 timezone，以便当前页面与后续前端逻辑读取一致的偏好值。

#### Scenario: 保存后会话偏好更新
- **WHEN** 用户保存新的 locale 和 timezone 且请求返回成功
- **THEN** 当前认证会话中的 locale 和 timezone MUST 更新为保存后的值

#### Scenario: 页面内后续消费者读取新偏好
- **WHEN** 保存成功后的页面内上下文、hooks 或组件再次读取用户偏好
- **THEN** 它们 MUST 读取到与最新保存结果一致的 locale 和 timezone

### Requirement: 后续请求必须按最新用户时区返回时间字段
用户保存新的 timezone 后，系统 MUST 使后续请求在无需重新登录的前提下，以最新用户时区返回时间相关字段。

#### Scenario: 后续接口返回新时区时间
- **WHEN** 用户保存新的 timezone 后发起新的受认证请求
- **THEN** 返回的关键时间字段 MUST 按最新用户 timezone 序列化

#### Scenario: 认证链路使用最新时区
- **WHEN** 服务端处理保存成功后的后续受认证请求
- **THEN** 请求上下文中的用户 timezone MUST 与最新保存的 timezone 一致