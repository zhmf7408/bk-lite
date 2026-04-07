# create_monitor_instance 使用说明

## 作用

`create_monitor_instance` 用于通过 YAML 文件调用监控接入流程，等价于后端执行：

```python
InstanceConfigService.create_monitor_instance_by_node_mgmt(request.data)
```

适用于把页面上的“接入监控实例”流程命令化调用。

## 命令格式

在 `server/` 目录下执行：

```bash
uv run python manage.py create_monitor_instance --config request.yaml --output result.yaml
```

## 参数说明

### 必填参数

- `--config`：请求 YAML 文件路径
- `--output`：结果 YAML 文件路径

## request.yaml 结构

### 顶层必填字段

- `monitor_object_id`
- `collector`
- `collect_type`
- `configs`
- `instances`

### configs 数组要求

每个 `configs[]` 元素必须是对象，且至少包含：

- `type`

### instances 数组要求

每个 `instances[]` 元素必须是对象，且至少包含：

- `instance_id`
- `instance_name`
- `group_ids`

其中：

- `group_ids` 必须是数组

## 完整示例

```yaml
monitor_object_id: 5
collector: telegraf
collect_type: host
monitor_plugin_id: 12
configs:
  - type: cpu
    interval: 10s
  - type: mem
    interval: 10s
instances:
  - instance_id: host-10.0.0.1
    instance_name: host-10.0.0.1
    group_ids:
      - 1
      - 2
    node_ids:
      - node-001
```

## 执行示例

```bash
uv run python manage.py create_monitor_instance --config request.yaml --output result.yaml
```

执行成功后，终端会输出：

```text
创建监控实例成功，结果文件已生成: result.yaml
```

## result.yaml 结构

输出文件包含两部分：

- `request`：原始请求参数
- `result`：创建结果

其中 `result` 当前包含：

- `status`
- `instances`

`result.instances[]` 中会返回实际创建后的实例信息，包含：

- `instance_id`
- `instance_id_values`
- `instance_name`
- `monitor_object_id`
- `monitor_object_name`
- `organizations`
- `interval`
- `is_active`
- `is_deleted`
- `auto`
- `configs`
- `created_at`
- `updated_at`

## 输出示例

```yaml
request:
  monitor_object_id: 5
  collector: telegraf
  collect_type: host
  monitor_plugin_id: 12
  configs:
    - type: cpu
      interval: 10s
  instances:
    - instance_id: host-10.0.0.1
      instance_name: host-10.0.0.1
      group_ids:
        - 1
        - 2
      node_ids:
        - node-001
result:
  status: success
  instances:
    - instance_id: "('host-10.0.0.1',)"
      instance_id_values:
        - host-10.0.0.1
      instance_name: host-10.0.0.1
      monitor_object_id: 5
      monitor_object_name: Host
      organizations:
        - 1
        - 2
      interval: 10
      is_active: true
      is_deleted: false
      auto: false
      configs:
        - id: xxx
          collector: telegraf
          collect_type: host
          config_type: cpu
          monitor_plugin_id: 12
          is_child: true
      created_at: "2026-04-07T13:00:00+08:00"
      updated_at: "2026-04-07T13:00:00+08:00"
```

## 常见错误

### 缺少必填参数

```text
缺少必填参数: monitor_object_id, collector
```

### YAML 文件不存在

```text
YAML 配置文件不存在: request.yaml
```

### YAML 格式错误

```text
YAML 配置解析失败: ...
```

### configs 非法

```text
configs 必须是非空数组
configs[0].type 必填
```

### instances 非法

```text
instances 必须是非空数组
instances[0].instance_id 必填
instances[0].instance_name 必填
instances[0].group_ids 必填
instances[0].group_ids 必须是数组
```

### 业务异常

命令会直接透传后端创建流程中的业务错误，例如：

```text
实例 'xxx' 已存在采集配置，无法重复创建。
```

## 建议

- 先用单实例 YAML 验证字段正确性，再扩展为批量实例
- `result.yaml` 可作为调用方保存创建结果和查询实例信息的落盘文件
