from apps.cmdb.collection.collect_plugin.protocol import ProtocolCollectMetrics
from apps.cmdb.collection.plugins.community.protocol.base import BaseProtocolCollectionPlugin


class MssqlCollectionPlugin(BaseProtocolCollectionPlugin):
    supported_model_id = "mssql"
    metric_names = ("mssql_info_gauge",)
    field_mapping = {
        "inst_name": ProtocolCollectMetrics.get_inst_name,
        "ip_addr": "ip_addr",
        "port": "port",
        "version": "version",
        "db_name": "db_name",
        "max_conn": "max_conn",
        "max_mem": "max_mem",
        "order_rule": "order_rule",
        "fill_factor": "fill_factor",
        "boot_account": "boot_account",
    }