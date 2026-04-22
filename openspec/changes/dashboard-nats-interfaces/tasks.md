## 1. CMDB 统计接口

- [x] 1.1 在 `server/apps/cmdb/nats/nats.py` 中实现 `get_cmdb_statistics` 接口，返回模型总数、实例总数、分类总数
- [x] 1.2 在 `server/apps/cmdb/nats/nats.py` 中实现 `get_change_trend` 接口，基于 `ChangeRecord` 模型统计变更趋势（新增/修改/删除）
- [x] 1.3 在 `server/apps/cmdb/nats/nats.py` 中实现 `get_instance_group_by` 接口，支持按指定字段分组统计实例（如主机按 os_type 统计）
- [x] 1.4 在 `server/apps/cmdb/nats/nats.py` 中实现 `get_model_inst_statistics` 接口，返回模型统计表格数据（分类、模型、数量）

## 2. Alerts 统计接口

- [x] 2.1 在 `server/apps/alerts/nats/nats.py` 中实现 `get_alert_statistics` 接口，返回告警/事件/事故各类计数
- [x] 2.2 在 `server/apps/alerts/nats/nats.py` 中实现 `get_alert_level_distribution` 接口，返回告警等级分布（支持活跃/全部过滤）
- [x] 2.3 在 `server/apps/alerts/nats/nats.py` 中实现 `get_active_alert_top` 接口，返回活跃告警持续时间 TOP N

## 3. 验证

- [x] 3.1 执行 `cd server && make lint` 确保代码风格符合规范
- [ ] 3.2 手动验证：通过仪表盘数据源配置调用新接口，确认返回数据格式正确
