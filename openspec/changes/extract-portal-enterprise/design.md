## Context

当前“设置 / 门户”页面、菜单项和默认实现都直接放在 `web/src/app/system-manager/` 下，社区版和商业版共享同一份菜单定义。这导致一旦某个能力只想在商业版出现，就只能继续把差异写进社区版主干，或者维护两份接近重复的页面与菜单文件。

本次变更先以“门户”作为第一个抽离对象，在当前项目内引入一个 `enterprise` 扩展层，验证后续“社区主干 + 商业 overlay”模式是否能在 BK-Lite 的现有 Next.js 应用结构中工作。约束包括：

- 现有 `/api/menu` 已支持从各 app 的 `menu.json` 读取菜单并应用 patch
- `NEXTAPI_INSTALL_APP` 已用于控制前端 app 扫描范围
- `/system-manager/settings/portal` 已经是既有访问路径，不能随意修改
- 现有 portal settings API 和数据项已经在线上使用，不宜迁移

## Goals / Non-Goals

**Goals:**
- 将“门户”从社区版默认菜单中抽离，使社区版默认不再展示该菜单项
- 保留 `/system-manager/settings/portal` 作为稳定路由入口，避免已存在链接和配置失效
- 在当前项目目录下新增 `enterprise` 扩展层，承载门户菜单 patch 和页面实现
- 让社区版在没有 enterprise 实现时仍能安全构建和运行
- 为后续其它“挂载到既有模块下的商业功能”复用同一扩展模式

**Non-Goals:**
- 本次不处理独立一级商业模块（如独立图表系统）的接入模式
- 本次不拆分后端 portal settings API；仍复用现有 system settings 接口
- 本次不建设完整双仓装配流水线；仅在当前仓库中落地 overlay 目录结构
- 本次不泛化为所有模块的统一插件系统，仅覆盖 system-manager/portal 这一路径

## Decisions

### 1. 在当前仓库根目录新增 `enterprise/`，并按 `enterprise/web`、`enterprise/server` 作为 overlay 根目录

将商业版增量实现收敛到仓库根目录的 `enterprise/` 下，而不是继续散落在 `web/` 或 `system-manager` 主目录中。这样可以让当前仓库里的 `enterprise/` 直接对齐未来商业版 submodule 的挂载位置：前端增量位于 `enterprise/web`，后端增量位于 `enterprise/server`。

备选方案：
- 继续把商业实现放在 `web/src/app/system-manager/enterprise/`：接入简单，但企业增量仍然与社区模块目录强耦合
- 直接新建独立仓库：长期更干净，但当前改造成本更高，不适合先验证模式

### 2. 社区版保留稳定路由页，实际页面通过 alias + stub 加载 enterprise 实现

`/system-manager/settings/portal` 继续保留在社区版目录中，但改为轻量入口页，只负责加载 enterprise 实现。若 enterprise 页面不存在，则回退到受控 stub，而不是让构建时报模块缺失错误。

这样既保留既有 URL，又把真实实现从社区版主干中挪出。

备选方案：
- 直接删除社区路由：会破坏既有链接和权限映射
- 让社区路由里保留完整页面实现，再在企业版覆盖：仍然保留了重复实现和主干耦合

### 3. 菜单采用“基础菜单 + enterprise patch”合并，而不是修改社区版菜单文件

`system-manager` 的基础菜单继续由社区版 `menu.json` 定义，但去掉 `portal` 子菜单。enterprise 目录额外提供 patch 文件，将 `portal_settings` 插入到“设置”分组下。

这样社区版菜单保持干净，商业能力通过增量 patch 接入，不需要长期维护两份基础菜单。

备选方案：
- 在社区版菜单里加 `if enterprise`：会把商业条件判断扩散到主干
- 商业版直接复制完整 `menu.json`：后续合并社区更新时冲突会持续增加

### 4. 继续复用现有 portal 配置接口和数据键

页面抽离只影响前端菜单与页面实现的组织方式，不调整现有 `portal_name`、`portal_logo_url`、`portal_favicon_url`、`watermark_*` 的读取和写入路径。

这样可以把这次改造的变量控制在“前端结构拆分”层面，避免把后端与数据迁移混在同一次变更中。

## Risks / Trade-offs

- **[Risk] overlay 目录扫描规则新增后，菜单加载逻辑更复杂** → 仅对 enterprise 目录增加单一入口和明确命名约定，避免引入通用插件系统
- **[Risk] stub 回退策略如果过于宽松，可能掩盖企业页面缺失问题** → 社区版允许安全回退，但企业版构建和测试需要显式校验 portal overlay 是否存在
- **[Risk] 现有权限过滤依赖 `portal_settings` 名称，菜单抽离后若命名变化会导致菜单被过滤掉** → 保持 `portal_settings` 作为稳定菜单名，不改已有权限映射
- **[Trade-off] 当前先在单仓中引入 `enterprise/` 目录并模拟 submodule 边界，而不是直接接入真实商业仓库** → 短期验证成本更低，但后续仍需把该目录替换为实际 submodule
