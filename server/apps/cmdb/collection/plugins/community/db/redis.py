from apps.cmdb.collection.plugins.community.db.base import BaseDBCollectionPlugin


class RedisCollectionPlugin(BaseDBCollectionPlugin):
    supported_model_id = "redis"
    metric_names = ("redis_info_gauge",)
    field_mapping = {
        "inst_name": BaseDBCollectionPlugin.get_inst_name,
        "ip_addr": "ip_addr",
        "port": "port",
        "version": "version",
        "install_path": "install_path",
        "max_conn": "max_conn",
        "max_mem": "max_mem",
        "database_role": "database_role",
        "topo_mode": "topo_mode",
        "cluster_uuid": "cluster_uuid",
        "slaves": "slaves",
        "master": "master",
    }