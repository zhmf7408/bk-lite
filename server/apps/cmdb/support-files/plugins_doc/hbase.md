### 说明
基于脚本采集本机 HBase Master 进程，解析启动参数与 `hbase-site.xml` 配置，采集版本、端口、安装路径、日志路径、Java 信息与关键运行参数，同步至 CMDB。

### 前置要求
1. HBase 已启动，且主机上存在 `org.apache.hadoop.hbase.master.HMaster` 进程。
2. 采集节点可通过 SSH 执行脚本。

### 版本兼容性
- 面向 Linux 环境下的 HBase Master 实例发现。

### 采集内容
| Key 名称                          | 含义                                  |
| :-------------------------------- | :------------------------------------ |
| inst_name                         | 实例展示名：`{内网IP}-hbase-{端口}`   |
| obj_id                            | 固定对象标识 `hbase`                  |
| ip_addr                           | 主机内网 IP                           |
| port                              | HBase Master 服务端口                 |
| version                           | HBase 版本                            |
| install_path                      | 安装路径                              |
| log_path                          | 日志目录                              |
| config_file                       | `hbase-site.xml` 配置文件绝对路径     |
| tmp_dir                           | 临时目录                              |
| cluster_distributed               | 是否分布式部署                        |
| java_path                         | Java 可执行文件路径                   |
| java_version                      | Java 版本                             |

> 补充说明：当前脚本只发现本机运行中的 HBase Master 实例，不采集 RegionServer、Backup Master、ZooKeeper 拓扑或 HDFS 关系；若未找到 `hbase` 可执行文件，则本次采集返回空结果。
