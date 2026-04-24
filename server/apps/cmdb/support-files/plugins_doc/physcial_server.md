### 说明
支持两条物理服务器自动发现链路：

1. **SSH 采集**：通过主机侧命令采集 CPU、内存、磁盘、网卡、GPU 等完整硬件资产信息。
2. **IPMI 采集**：通过 BMC / IPMI 管理口采集物理服务器基础身份信息，用于带外资产补充。

> `physcial_server.ip_addr` 在 IPMI 采集场景下表示 **IPMI 管理口 IP**，不是业务网口地址。

### 前置要求

#### SSH 采集
1. 已开通 SSH 访问（默认端口 22，可自定义），网络连通。
2. 采集账号具备只读执行权限：`dmidecode`、`lscpu`、`lsblk`、`lspci`、`smartctl`、`nvme` 等命令可按需执行。

#### IPMI 采集
1. 已开通 BMC / IPMI 管理口访问，默认端口 623。
2. 提供可用的 IPMI 用户名与密码；可按需指定 `privilege`，默认使用管理员级别。
3. 目标设备支持标准 IPMI / FRU inventory 能力，不保证所有厂商返回相同字段。

### IPMI 一期采集内容
| 字段 | 说明 |
| :--- | :--- |
| `ip_addr` | IPMI 管理口 IP |
| `serial_number` | 序列号 |
| `model` | 产品型号 |
| `brand` | 厂商 |
| `asset_code` | 资产标签（若 FRU 提供） |
| `board_vendor` | 主板厂商 |
| `board_model` | 主板型号 |
| `board_serial` | 主板序列号 |

### 边界说明
1. IPMI 采集仅补充 **基础身份字段**，不替代现有 SSH 物理服务器全量硬件采集。
2. IPMI 采集 **不会创建** `memory` / `disk` / `nic` / `gpu` 关联实例。
3. IPMI 路径只更新白名单字段，空值不会覆盖已有 SSH 采集写入的非空字段。
4. `operator`、`cabinet`、`room`、`asset_status` 等业务字段不由 IPMI 自动采集。

### 常见限制
1. `asset_code`、`board_serial` 等字段依赖厂商 FRU 实现，可能为空。
2. `cpu_*`、完整内存/磁盘/网卡/GPU 信息通常不能稳定依赖纯 IPMI 获取。
3. 如果 BMC 不通、认证失败或协议超时，任务会失败；如果只是部分字段缺失，任务允许部分成功。
