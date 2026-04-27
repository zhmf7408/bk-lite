## Why

运营分析仪表盘需要展示 CMDB 和告警的统计数据，包括单值组件（模型总数、实例总数、告警总数等）、趋势图（变更趋势、告警趋势）、饼状图（主机按 OS 统计、告警等级分布）和表格（模型统计、活跃告警 TOP 10）。

当前已有的 NATS 接口无法满足这些场景：
- CMDB 模块缺少统计类接口（模型/实例计数、变更趋势、分组统计）
- Alerts 模块仅有 `get_alert_trend_data` 趋势接口，缺少计数和分布统计接口

## What Changes

- 在 CMDB 模块新增 4 个 NATS 接口：统计数据、变更趋势、实例分组统计、模型实例统计
- 在 Alerts 模块新增 3 个 NATS 接口：告警统计、等级分布、活跃告警 TOP N
- 所有接口遵循现有 NATS 注册模式（`@nats_client.register`）
- CMDB 接口支持组织过滤（与 `query_asset_instances` 一致）
- Alerts 接口不加组织过滤（与 `get_alert_trend_data` 一致）

## Capabilities

### New Capabilities
- `cmdb-dashboard-statistics`: CMDB 仪表盘统计数据接口，支持模型/实例计数、变更趋势、分组统计
- `alerts-dashboard-statistics`: 告警仪表盘统计数据接口，支持告警/事件/事故计数、等级分布、活跃告警排行

### Modified Capabilities
- 无

## Impact

- `server/apps/cmdb/nats/nats.py`: 新增 4 个 NATS 接口
- `server/apps/alerts/nats/nats.py`: 新增 3 个 NATS 接口
- 依赖现有数据模型：`ChangeRecord`、`Alert`、`Event`、`Incident`
- 依赖现有服务：`ModelManage`、`ClassificationManage`、`InstanceManage`
