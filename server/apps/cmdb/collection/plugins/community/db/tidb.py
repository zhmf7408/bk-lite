from apps.cmdb.collection.plugins.community.db.base import BaseDBCollectionPlugin


class TiDBCollectionPlugin(BaseDBCollectionPlugin):
    supported_model_id = "tidb"
    metric_names = ("tidb_info_gauge",)
    field_mapping = {
        "inst_name": BaseDBCollectionPlugin.get_inst_name,
        "ip_addr": "ip_addr",
        "port": "port",
        "version": "version",
        "db_name": "db_name",
        "install_path": "install_path",
        "home_bash": "home_bash",
        "db_max_sessions": "db_max_sessions",
        "redo_log": "redo_log",
        "datafile": "datafile",
        "mode": "mode",
    }
