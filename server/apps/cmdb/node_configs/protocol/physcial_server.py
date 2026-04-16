# -- coding: utf-8 --
from apps.cmdb.node_configs.base import BaseNodeParams


class PhysicalServerIPMINodeParams(BaseNodeParams):
    supported_model_id = "physcial_server"
    supported_driver_type = "protocol"
    # 复用现有 physcial_server 插件目录，但通过 protocol executor 走带外 IPMI 采集逻辑。
    plugin_name = "physcial_server_info"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host_field = "ip_addr"
        self.executor_type = "protocol"

    def set_credential(self, *args, **kwargs):
        password_key = f"PASSWORD_password_{self._instance_id}"
        credential_data = {
            # ip_addr 在本条链路中明确表示 BMC / IPMI 管理口地址，而不是业务网口地址。
            "port": self.credential.get("port", 623),
            "username": self.credential.get("username", self.credential.get("user", "")),
            "password": "${" + password_key + "}",
        }
        privilege = self.credential.get("privilege")
        if privilege:
            credential_data["privilege"] = privilege
        return credential_data

    def env_config(self, *args, **kwargs):
        return {
            f"PASSWORD_password_{self._instance_id}": self.credential.get("password", ""),
        }
