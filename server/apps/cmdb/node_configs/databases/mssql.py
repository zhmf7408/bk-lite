# -- coding: utf-8 --
# @File: mssql.py
# @Time: 2026/04/14 23:49
# @Author: Sisyphus

from apps.cmdb.node_configs.base import BaseNodeParams


class MssqlNodeParams(BaseNodeParams):
    supported_model_id = "mssql"
    plugin_name = "mssql_info"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.PLUGIN_MAP.update({self.model_id: self.plugin_name})
        self.host_field = "ip_addr"
        self.executor_type = "protocol"

    def set_credential(self, *args, **kwargs):
        _password = f"PASSWORD_password_{self._instance_id}"
        return {
            "port": self.credential.get("port", 1433),
            "user": self.credential.get("user", ""),
            "password": "${" + _password + "}",
            "database": self.credential.get("database", "master"),
        }

    def env_config(self, *args, **kwargs):
        return {f"PASSWORD_password_{self._instance_id}": self.credential.get("password", "")}
