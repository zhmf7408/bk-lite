## Why

当商业版代码通过 submodule 挂在仓库根目录 `enterprise/` 下时，菜单、页面、语言包和静态资源不再与社区版 `web/` 同目录。若继续依赖社区版手写页面 loader 或静态 import 商业页面，社区版构建会被商业页面反向污染，也无法支撑后续商业版独立扩展。

## What Changes

- 定义 `web/enterprise` 作为社区版前端对商业代码的统一消费入口，约定其通过 manifest 描述菜单 patch 和页面路由来源。
- 为商业版页面引入 build-time route shim 机制：社区版构建前根据 `web/enterprise` 的路由 manifest 自动生成 Next App Router 所需的 page shim。
- 保留现有社区版菜单/语言包/静态资源合并流程，并扩展为可直接扫描 `web/enterprise` 的菜单、locales 和 public 资源。
- 明确社区版单独构建时的行为：当 `web/enterprise` 不存在时，构建必须跳过商业版装配，不得因为缺少商业代码而失败。
- 为后续根目录 submodule 下的商业前端功能提供统一接入协议，避免每新增一个商业页面就要求社区版手写对应 loader。

## Capabilities

### New Capabilities
- `enterprise-submodule-route-assembly`: 定义 `web/enterprise` 如何通过 manifests、资源扫描和 build-time route shims 接入社区版前端构建。

### Modified Capabilities

## Impact

- **Web 构建与装配**:
  - `web/scripts/prepare-enterprise.mjs` 或同类构建前脚本
  - `web/src/utils/dynamicsMerged.mjs`
  - `web/src/app/(core)/api/menu/route.ts`
  - Next 构建输入目录与生成的 route shim 目录
- **商业版 submodule 协议**:
  - `web/enterprise/manifests/routes.json`
  - `web/enterprise/manifests/menus.json`
  - `web/enterprise/src/app/**`
  - `web/enterprise/public/**`
- **开发与发布流程**:
  - 社区版单独构建流程
  - 商业版 submodule 已拉取时的前端构建流程
