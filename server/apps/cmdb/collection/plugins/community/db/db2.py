from apps.cmdb.collection.plugins.community.db.base import BaseDBCollectionPlugin


class DB2CollectionPlugin(BaseDBCollectionPlugin):
    supported_model_id = "db2"
    metric_names = ("db2_info_gauge",)
    field_mapping = {
        "inst_name": lambda data: f"{data['ip_addr']}-db2",
        "version": "version",
        "db_patch": "db_patch",
        "db_name": "db_name",
        "db_instance_name": "db_instance_name",
        "ip_addr": "ip_addr",
        "port": "port",
        "db_character_set": "db_character_set",
        "ha_mode": "ha_mode",
        "replication_managerole": "replication_managerole",
        "replication_role": "replication_role",
        "data_protect_mode": "data_protect_mode",
    }