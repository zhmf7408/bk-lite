from apps.cmdb.collection.collect_plugin.protocol import ProtocolCollectMetrics
from apps.cmdb.collection.plugins.community.protocol.base import BaseProtocolCollectionPlugin


class PostgresqlCollectionPlugin(BaseProtocolCollectionPlugin):
    supported_model_id = "postgresql"
    metric_names = ("postgresql_info_gauge",)
    field_mapping = {
        "inst_name": ProtocolCollectMetrics.get_inst_name,
        "ip_addr": "ip_addr",
        "port": "port",
        "version": "version",
        "config": "conf_path",
        "data_path": "data_path",
        "max_connect": "max_conn",
        "shared_buffer": "cache_memory_mb",
        "log_directory": "log_path",
    }