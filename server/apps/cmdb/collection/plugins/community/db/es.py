from apps.cmdb.collection.plugins.community.db.base import BaseDBCollectionPlugin


class ESCollectionPlugin(BaseDBCollectionPlugin):
    supported_model_id = "es"
    metric_names = ("es_info_gauge",)
    field_mapping = {
        "inst_name": BaseDBCollectionPlugin.get_inst_name,
        "ip_addr": "ip_addr",
        "port": "port",
        "version": "version",
        "log_path": "log_path",
        "data_path": "data_path",
        "is_master": "is_master",
        "node_name": "node_name",
        "cluster_name": "cluster_name",
        "java_version": "java_version",
        "java_path": "java_path",
        "conf_path": "conf_path",
        "install_path": "install_path",
    }