from apps.cmdb.collection.plugins.community.db.base import BaseDBCollectionPlugin


class TiDBCollectionPlugin(BaseDBCollectionPlugin):
    supported_model_id = "tidb"
    metric_names = ("tidb_info_gauge",)
    field_mapping = {
        "inst_name": BaseDBCollectionPlugin.get_inst_name,
        "ip_addr": "ip_addr",
        "port": "port",
        "version": "version",
        "dm_db_name": "dm_db_name",
        "dm_install_path": "dm_install_path",
        "dm_conf_path": "dm_conf_path",
        "dm_log_file": "dm_log_file",
        "dm_home_bash": "dm_home_bash",
        "dm_db_max_sessions": "dm_db_max_sessions",
        "dm_redo_log": "dm_redo_log",
        "dm_datafile": "dm_datafile",
        "dm_mode": "dm_mode",
    }