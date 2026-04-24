## Overview

`license-mgmt` 采用“系统管理公共路由壳 + 企业版真实页面实现 + 独立后端领域服务”的方式落地。社区版路由 `system-manager/(pages)/settings/license/page.tsx` 仅作为稳定入口，真实页面实现位于 `web/src/app/system-manager/enterprise/(pages)/settings/license/page.tsx`。后端能力由 `server/apps/license_mgmt` 承接，负责许可主数据、提醒配置、注册码读取、许可验签与新增资源校验。

## Key Decisions

### 1. 保持稳定入口，企业版承载真实页面

- Web 入口路径保持 `/system-manager/settings/license` 不变。
- 公共页面仅动态加载 enterprise 页面，避免把企业版业务代码直接放回公共设置页。
- 许可弹窗统一使用仓库现有 `OperateModal`，避免继续维护额外的自定义 modal 壳。

### 2. 提醒配置使用统一配置模型

- 全局默认提醒保存 `default_channel_ids`、`default_user_ids`、`default_remind_days`。
- 单许可提醒使用 `follow/custom` 模式切换；`custom` 时保存独立通知渠道、通知人员和提醒天数。
- 节点提醒保存模块级阈值和专用节点覆盖项；日志容量提醒保存 `follow/custom` 模式与阈值。
- 用户和渠道都以 ID 列表存储，保存前按当前用户可见范围校验。

### 3. 许可卡片状态直接由服务端提醒窗口判断驱动

- `LicenseService.serialize_license` 在返回 `reminder` 时同时输出 `warning` 与 `status`。
- `status=warning` 表示当前许可已进入提醒窗口；`status=healthy` 表示未进入提醒窗口。
- 前端许可卡片、剩余天数 badge 与提醒配置入口全部按该状态切换样式，不在页面层重复推导风险状态。

### 4. 资源新增拦截通过中间件 + RPC 完成

- `LicenseCreateGuardMiddleware` 先检查 `LICENSE_MGMT_ENABLED`，避免未启用环境误拦截。
- `PermissionGuardService` 根据 `LICENSE_APP_PERMISSIONS` 判断当前请求是否属于受控新增入口。
- 命中受控入口后，通过 `apps.rpc.license_mgmt.LicenseMgmt().validate_module_create_access(...)` 获取放行结果；拒绝时返回 403。

## Constraints

- 设计以当前仓库实际实现为准，不再保留旧的“待实现目录/阶段”描述。
- OpenSpec 归档前只记录已经存在的行为，不扩展尚未落地的新接口或新模块。
- 许可提醒页面样式以 `spec/prototype/系统管理/设置/许可.html` 为对齐基准，优先复用原型结构和仓库内现有组件。
