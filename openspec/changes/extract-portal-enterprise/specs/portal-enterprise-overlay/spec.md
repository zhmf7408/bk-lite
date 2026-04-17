## ADDED Requirements

### Requirement: 社区版默认不得展示门户菜单

系统管理基础菜单 MUST 在社区版默认构建中不包含 `portal_settings` 菜单项。

#### Scenario: 社区版仅加载基础菜单
- **WHEN** 系统仅加载社区版 `system-manager` 基础菜单源
- **THEN** “设置”分组下 MUST 不出现 `/system-manager/settings/portal` 菜单项

#### Scenario: enterprise patch 被注入后显示门户菜单
- **WHEN** 系统同时加载基础菜单和 enterprise portal 菜单 patch
- **THEN** “设置”分组下 MUST 追加名称为 `portal_settings`、URL 为 `/system-manager/settings/portal` 的菜单项

### Requirement: 门户页面必须通过稳定路由加载 enterprise overlay

系统 MUST 保留 `/system-manager/settings/portal` 作为稳定访问路径，并由该路径加载 enterprise overlay 中的真实页面实现。

#### Scenario: enterprise 页面存在时加载真实实现
- **WHEN** 用户访问 `/system-manager/settings/portal` 且 enterprise overlay 中存在门户页面实现
- **THEN** 系统 MUST 渲染 enterprise overlay 提供的门户设置页面

#### Scenario: enterprise 页面缺失时安全回退
- **WHEN** 用户访问 `/system-manager/settings/portal` 但当前构建中不存在 enterprise 门户页面实现
- **THEN** 系统 MUST 回退到受控 stub，而不能因为模块缺失导致构建失败

### Requirement: enterprise overlay 必须有明确的目录约定

系统 MUST 在当前仓库根目录提供明确的 `enterprise/` overlay 目录，并按 `enterprise/web`、`enterprise/server` 分离商业版增量实现。

#### Scenario: 页面实现位于 enterprise 目录
- **WHEN** 开发者为商业版提供门户页面实现
- **THEN** 该实现 MUST 放在当前项目约定的 enterprise 目录下，而不是继续放在社区版 `system-manager` 默认页面目录中

#### Scenario: 菜单 patch 位于 enterprise 目录
- **WHEN** 开发者为商业版追加门户菜单
- **THEN** 菜单 patch MUST 放在当前项目约定的 enterprise 目录下，并通过菜单加载流程合并到基础菜单树中

### Requirement: 门户抽离不得改变既有访问路径和配置键

系统 MUST 在门户抽离到 enterprise overlay 后保持现有门户访问路径和 portal settings 配置键不变。

#### Scenario: 已有入口链接继续可用
- **WHEN** 用户通过现有链接访问 `/system-manager/settings/portal`
- **THEN** 系统 MUST 继续使用该路径访问门户能力，而不能要求切换到新 URL

#### Scenario: 既有配置键继续生效
- **WHEN** enterprise 门户页面读取或保存门户配置
- **THEN** 系统 MUST 继续使用现有 portal settings 数据键，而不能引入新的迁移型配置键
