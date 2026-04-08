from apps.cmdb.collection.plugins.community.protocol.base import BaseProtocolCollectionPlugin


class OracleCollectionPlugin(BaseProtocolCollectionPlugin):
    supported_model_id = "oracle"
    metric_names = ("oracle_info_gauge",)
    field_mapping = {
        "version": "version",
        "max_mem": "max_mem",
        "max_conn": "max_conn",
        "db_name": "db_name",
        "database_role": "database_role",
        "sid": "sid",
        "ip_addr": "ip_addr",
        "port": "port",
        "service_name": "service_name",
        "inst_name": lambda self, data: f"{data['ip_addr']}-oracle",
    }