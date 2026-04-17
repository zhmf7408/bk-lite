## ADDED Requirements

### Requirement: 社区版构建必须支持 web/enterprise 缺失

系统 MUST 在 `web/enterprise` 不存在时继续完成社区版前端构建，而不能因为缺少商业版前端入口而失败。

#### Scenario: 社区版单独构建
- **WHEN** 前端构建启动且 `web/enterprise` 不存在
- **THEN** 系统 MUST 跳过商业版菜单、路由、语言包和静态资源装配，并继续完成社区版构建

#### Scenario: 商业版 submodule 已拉取时构建
- **WHEN** 前端构建启动且 `web/enterprise` 存在
- **THEN** 系统 MUST 读取商业版 manifests 和资源输入，并将其纳入构建装配流程

### Requirement: 商业页面路由必须通过 manifest 驱动的 build-time shim 接入

系统 MUST 支持商业版通过 `web/enterprise/manifests/routes.json` 声明页面路由来源，并在构建前生成 Next App Router 所需的 route shim。

#### Scenario: 为商业页面生成 shim
- **WHEN** `routes.json` 声明 `/system-manager/settings/portal` 对应的商业页面源文件
- **THEN** 系统 MUST 在社区版前端构建输入中生成对应的 page shim，并将该 URL 路由到商业页面实现

#### Scenario: 社区版不再手写商业页面 loader
- **WHEN** 新增一个商业版页面并在 `routes.json` 中注册
- **THEN** 系统 MUST 允许该页面通过构建期 shim 生效，而不要求社区版源码手写新的页面 loader

### Requirement: 商业菜单必须通过 manifest 注入社区菜单树

系统 MUST 支持商业版通过 `web/enterprise/manifests/menus.json` 声明菜单 patch，并将其合并到社区版基础菜单树中。

#### Scenario: 商业菜单 patch 被注入
- **WHEN** `menus.json` 声明向 `Setting` 节点追加 `portal_settings` 菜单项
- **THEN** 系统 MUST 在商业版构建或运行时菜单加载中，将该菜单项注入到基础菜单树

#### Scenario: 社区版不显示商业菜单
- **WHEN** `web/enterprise` 不存在或 `menus.json` 未提供对应 patch
- **THEN** 系统 MUST 不显示商业菜单项

### Requirement: 商业语言包与静态资源必须支持直接扫描合并

系统 MUST 支持从 `web/enterprise` 直接扫描并合并商业版 locales 与 public 资源。

#### Scenario: 合并商业语言包
- **WHEN** `web/enterprise/src` 下存在商业页面对应的 locale 文件
- **THEN** 系统 MUST 将这些 locale 内容合并到社区版最终语言包输出中

#### Scenario: 合并商业静态资源
- **WHEN** `web/enterprise/public` 下存在商业版静态资源
- **THEN** 系统 MUST 将这些资源纳入社区版构建输出，使商业页面可在构建产物中访问它们
