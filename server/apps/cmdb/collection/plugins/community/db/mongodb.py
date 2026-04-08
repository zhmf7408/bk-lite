from apps.cmdb.collection.plugins.community.db.base import BaseDBCollectionPlugin


class MongoDBCollectionPlugin(BaseDBCollectionPlugin):
    supported_model_id = "mongodb"
    metric_names = ("mongodb_info_gauge",)
    field_mapping = {
        "inst_name": BaseDBCollectionPlugin.get_inst_name,
        "ip_addr": "ip_addr",
        "port": "port",
        "version": "version",
        "mongo_path": "mongo_path",
        "bin_path": "bin_path",
        "config": "config",
        "fork": "fork",
        "system_log": "system_log",
        "db_path": "db_path",
        "max_incoming_conn": "max_incoming_conn",
        "database_role": "database_role",
    }