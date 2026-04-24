## Context

BK-Lite 计划让商业版代码独立维护在另一个仓库中，并通过 submodule 挂载到社区版仓库根目录 `enterprise/`。社区版前端通过 `web/enterprise -> ../enterprise/web` 软链接消费商业版前端代码，而社区版前端构建入口仍然固定在 `web/`。

现有社区版前端已经具备一定的菜单、语言包和静态资源合并能力，但页面路由仍依赖 Next App Router 的文件系统约束：最终参与构建的页面必须在社区版 `web` 的路由树里可见。如果继续让社区版手写每个商业页面 loader，不仅会污染社区版源码，也无法随着商业功能扩展而稳定维护。

## Goals / Non-Goals

**Goals:**
- 支持商业版前端代码通过 `web/enterprise` 接入社区版前端构建
- 让社区版单独构建时在没有 `web/enterprise` 的情况下仍然正常完成
- 用统一 manifest + build-time route shim 机制替代手写商业页面 loader
- 复用并扩展现有菜单、locales、public 资源合并机制，使其能从 `web/enterprise` 读取增量内容

**Non-Goals:**
- 本次不定义商业版后端 submodule 的完整装配协议
- 本次不要求把已有所有商业页面一次性迁移到 manifest 模式
- 本次不设计通用插件运行时；仍以构建期装配为主
- 本次不改变既有商业页面的最终访问 URL 约定

## Decisions

### 1. 商业版前端通过 `web/enterprise` 软链接接入

社区版构建脚本以 `web/` 为当前工作目录，通过 `web/enterprise -> ../enterprise/web` 软链接读取商业版前端输入。这样商业代码在社区版前端工程内有稳定入口，同时仍保留商业仓库的独立边界。

备选方案：
- 直接把商业版页面逐个软链接到 `web/src/app`：本地直观，但新增页面要单独挂载，长期维护成本更高
- 把商业页面继续散落到 `web/src/app`：最简单，但违反商业版独立仓库目标

### 2. 商业页面路由通过 build-time generated shim 接入 Next App Router

商业版 submodule 提供 `manifests/routes.json`，声明 URL 到商业页面源文件的映射。社区版在构建前根据该 manifest 自动生成 page shim，再由 Next 正常参与构建。

这样可以保留 `/system-manager/settings/portal` 这类原始 URL，同时避免社区版手写每个商业页面入口。

备选方案：
- 社区版手写页面 loader：实现简单，但每个商业页面都会反向污染社区主干
- 用统一 catch-all runtime router：实现更动态，但会改变现有 URL 和权限模型

### 3. 菜单、语言包、静态资源继续采用扫描式合并

商业版前端通过 `web/enterprise` 提供 `manifests/menus.json` 以及常规 `src/**/locales`、`public/**` 目录。社区版构建与运行时接口直接扫描这些输入并合并，不为每个商业资源再单独设计加载器。

这样把复杂度集中在“页面路由必须生成 shim”这一点，其它资源沿用已有的聚合模型。

### 4. 社区版构建时必须显式容忍 submodule 缺失

所有读取 `web/enterprise` 的逻辑都必须先检查目录是否存在。不存在时：
- 菜单 patch 不注入
- route shim 不生成
- locales/public 不合并
- 整体构建继续完成

这样社区版单独出包时不会因为商业版 submodule 没拉取而失败。

## Risks / Trade-offs

- **[Risk] route manifest 与真实源文件不一致会导致生成的 shim 无效** → 在构建前脚本中增加 manifest 校验和明确错误输出
- **[Risk] 生成 shim 会让调试路径多一层跳转** → 当前实现改为在构建前物化路由文件内容，避免 Next/Turbopack 对跨根目录 route import 的解析限制，同时保留 manifest 驱动和无手写 loader 的目标
- **[Trade-off] 页面路由需要生成中间文件，而菜单/locales/public 可直接扫描** → 接受两种接入方式并存，以适配 Next 的文件系统路由限制
- **[Risk] 社区构建和商业构建路径不一致可能带来遗漏** → 统一由 `prepare-enterprise` 脚本控制，社区/商业 build 都走同一装配入口
