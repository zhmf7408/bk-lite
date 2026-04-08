from apps.cmdb.collection.collect_plugin.protocol import ProtocolCollectMetrics
from apps.cmdb.collection.plugins.community.protocol.base import BaseProtocolCollectionPlugin


class MysqlCollectionPlugin(BaseProtocolCollectionPlugin):
    supported_model_id = "mysql"
    metric_names = ("mysql_info_gauge",)
    field_mapping = {
        "ip_addr": "ip_addr",
        "port": "port",
        "version": "version",
        "enable_binlog": "enable_binlog",
        "sync_binlog": "sync_binlog",
        "max_conn": "max_conn",
        "max_mem": "max_mem",
        "basedir": "basedir",
        "datadir": "datadir",
        "socket": "socket",
        "bind_address": "bind_address",
        "slow_query_log": "slow_query_log",
        "slow_query_log_file": "slow_query_log_file",
        "log_error": "log_error",
        "wait_timeout": "wait_timeout",
        "inst_name": ProtocolCollectMetrics.get_inst_name,
    }