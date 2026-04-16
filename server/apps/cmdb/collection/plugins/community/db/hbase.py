from apps.cmdb.collection.plugins.community.db.base import BaseDBCollectionPlugin


class HBaseCollectionPlugin(BaseDBCollectionPlugin):
    supported_model_id = "hbase"
    metric_names = ("hbase_info_gauge",)

    field_mapping = {
        "inst_name": BaseDBCollectionPlugin.get_inst_name,
        "ip_addr": "ip_addr",
        "port": "port",
        "version": "version",
        "install_path": "install_path",
        "log_path": "log_path",
        "config_file": "config_file",
        "tmp_dir": "tmp_dir",
        "cluster_distributed": "cluster_distributed",
        "java_path": "java_path",
        "java_version": "java_version",
    }
