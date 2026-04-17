## Context

当前 Redis 内置工具的配置元数据来自 `CONSTRUCTOR_PARAMS`，最终在 `SkillTools.params.kwargs` 中表现为一组固定字段。技能保存时，所填值被写入 `LLMSkill.tools[].kwargs`；执行时 `chat_service` 会把这些键值对合并进 `extra_config`，再透传到 LangGraph `configurable`。Redis 连接层 `redis/connection.py` 只读取 `url`、`username`、`password`、`ssl`、`cluster_mode` 等单实例字段。

这条链路决定了当前能力上限：

- 同一个 Redis 工具只能表达一套连接参数。
- 如果尝试塞入两套同名字段，后写值会覆盖先写值。
- 现有技能工具编辑器对大多数内置工具是通用表单，不足以承载“左侧实例列表 + 右侧实例详情 + 单实例测试状态”的 Redis 专属交互。

## Goals / Non-Goals

**Goals:**
- 让单个智能体内的 Redis 工具支持维护多个 Redis 实例。
- 提供与产品草图一致的实例级配置体验，包括默认命名、新增/删除、实例级测试连接和状态展示。
- 将 Redis 运行时配置升级为多实例协议，避免同名参数互相覆盖。
- 保持 Redis 子工具默认可在未指定实例时使用默认实例，并在需要时切换到指定实例。

**Non-Goals:**
- 不重写所有内置工具的通用参数协议，仅收敛 Redis 工具的多实例场景。
- 不要求保存前必须测试成功，测试连接仅作为配置校验辅助。
- 不在本次变更中扩展 Redis 工具的权限模型或引入新的外部 Redis 管理服务。

## Decisions

### 1. Redis 工具以单个 tool 持有多个实例，而不是复制多个 Redis tool

技能中仍然只选择一次 Redis 工具，但该工具的配置值改为持有 `instances[]` 与 `default_instance_id`。

选择原因：用户心智是“给一个智能体配置多个 Redis 实例”，而不是“在智能体上挂多个外观相同的 Redis 工具”。保持单个工具入口也能避免工具列表、权限配置与模型理解上的重复噪音。

备选方案：
- 为每个 Redis 实例复制一个独立 tool。否决，因为当前执行链路仍会把 Redis 连接键拍平，且会让工具选择与展示变得混乱。

### 2. 多实例配置作为 Redis tool 自有契约存储为命名字段

Redis 工具不再依赖 `url`、`username`、`password` 等直接平铺到技能工具值中，而是将完整配置收敛为如下键：

- `redis_instances`
- `redis_default_instance_id`

其中 `redis_instances` 的值为 JSON 结构，包含多个实例及其连接属性。

选择原因：这样可以在不推翻通用 `kwargs -> extra_config` 合并流程的前提下，避免多实例字段覆盖问题，并把改动范围集中在 Redis 工具自身。

### 3. Redis 工具编辑器采用专属 UI，而不是复用通用 kwargs 表单

前端对 Redis 内置工具增加专属编辑器：

- 左侧：实例列表，支持新增/删除与选中
- 右侧：当前实例详情表单
- 右上角：当前实例测试状态
- 底部：测试连接 / 取消 / 保存

实例名称默认按 `Redis - n` 生成；当用户修改实例任一连接字段后，该实例状态立即回到“未测试”。

选择原因：截图中的交互是面向实例集合的编辑模型，通用 `Form.List(kwargs)` 无法自然表达实例列表、选中态和局部状态复位。

### 4. 测试连接为实例级后端接口，状态只针对当前编辑数据

后端提供 Redis 实例测试连接接口，输入为单个实例的当前表单值，输出为 `success/failure` 及错误信息。前端根据返回结果将该实例状态显示为：

- `untested`
- `success`
- `failed`

状态用于当前编辑会话中的反馈，不作为长期事实写入技能配置；当实例字段变更后状态重置为 `untested`。

选择原因：测试状态的意义是“当前配置是否可连通”，而不是一条可长期持久化的资产健康记录。持久化最后一次结果既容易过期，也会让编辑回显产生误导。

### 5. Redis 运行时增加“默认实例 + 显式实例”两级选择

Redis 连接层新增如下行为：

- 若工具调用未提供实例标识，则使用 `redis_default_instance_id`
- 若提供 `instance_id` 或 `instance_name`，则解析到对应实例后建立连接
- 若指定实例不存在，则返回明确错误

Redis 各子工具共享同一套实例解析逻辑。

选择原因：默认实例保证简单请求不增加负担，显式实例则满足多 Redis 管理的核心场景。

### 6. Redis 工具提示中展示可用实例名称

在 Redis 工具装载时，系统应把当前已配置的实例名称列表加入工具描述或附加提示，帮助模型在需要跨实例操作时显式选择正确实例。

选择原因：即便后端支持 `instance_name`，模型也需要知道有哪些可选实例名，才能稳定地产生正确调用。

## Data Shape

### Skill tool kwargs

```json
[
  {
    "key": "redis_instances",
    "value": "[{\"id\":\"redis-1\",\"name\":\"redis-prod-01\",\"url\":\"redis://10.0.1.15:6379/0\",\"username\":\"\",\"password\":\"\",\"ssl\":false,\"ssl_ca_path\":\"\",\"ssl_keyfile\":\"\",\"ssl_certfile\":\"\",\"ssl_cert_reqs\":\"\",\"ssl_ca_certs\":\"\",\"cluster_mode\":false}]"
  },
  {
    "key": "redis_default_instance_id",
    "value": "redis-1"
  }
]
```

### Parsed runtime config

```json
{
  "redis_instances": [
    {
      "id": "redis-1",
      "name": "redis-prod-01",
      "url": "redis://10.0.1.15:6379/0",
      "username": "",
      "password": "",
      "ssl": false,
      "ssl_ca_path": "",
      "ssl_keyfile": "",
      "ssl_certfile": "",
      "ssl_cert_reqs": "",
      "ssl_ca_certs": "",
      "cluster_mode": false
    },
    {
      "id": "redis-2",
      "name": "Redis - 2",
      "url": "",
      "username": "",
      "password": "",
      "ssl": false,
      "ssl_ca_path": "",
      "ssl_keyfile": "",
      "ssl_certfile": "",
      "ssl_cert_reqs": "",
      "ssl_ca_certs": "",
      "cluster_mode": false
    }
  ],
  "redis_default_instance_id": "redis-1"
}
```

### Tool call shape

```json
{
  "instance_name": "redis-prod-01",
  "key": "user:1"
}
```

`instance_name` / `instance_id` 为可选字段；未提供时走默认实例。

## Risks / Trade-offs

- Redis 工具将成为第一个需要专属编辑器的内置工具，前端工具编辑流程会出现“通用表单 + 特殊工具表单”双路径。
- `redis_instances` 若以 JSON 字符串保存在 kwargs 中，前后端都需要处理解析与校验错误，但这是换取最小通用协议改动的结果。
- 若模型不显式指定实例，所有操作都会落到默认实例，因此默认实例的设置与提示文案必须足够清晰。
- 旧的单实例 Redis 配置需要迁移或兼容读取，否则已有技能中的 Redis 工具可能需要重新保存。

## Migration Plan

1. 前端先支持读取旧单实例 Redis 配置，并在编辑时转换为单元素 `instances[]`。
2. 保存后统一写入新协议：`redis_instances` + `redis_default_instance_id`。
3. 后端 Redis 连接层优先读取新协议；若未发现新协议，可临时回退读取旧单实例键，保证已存在技能不中断。
4. 发布说明中明确：Redis 工具已支持多实例，重新编辑并保存可完成配置协议升级。

## Open Questions

- 是否需要在 UI 中允许用户显式切换“默认实例”，还是默认取列表第一项并仅在删除/新增时自动维护。
- 旧单实例配置的兼容回退需要保留一个版本周期，还是允许只在编辑页做一次性转换。
