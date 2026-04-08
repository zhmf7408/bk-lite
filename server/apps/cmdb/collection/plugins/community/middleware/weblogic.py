from apps.cmdb.collection.collect_plugin.middleware import MiddlewareCollectMetrics
from apps.cmdb.collection.plugins.community.middleware.base import BaseMiddlewareCollectionPlugin


class WeblogicCollectionPlugin(BaseMiddlewareCollectionPlugin):
    supported_model_id = "weblogic"
    metric_names = ("weblogic_info_gauge",)
    field_mapping = {
        "inst_name": MiddlewareCollectMetrics.get_inst_name,
        "bk_obj_id": "bk_obj_id",
        "ip_addr": "ip_addr",
        "port": "port",
        "wlst_path": "wlst_path",
        "java_version": "java_version",
        "domain_version": "domain_version",
        "admin_server_name": "admin_server_name",
        "name": "name",
        "assos": MiddlewareCollectMetrics.get__host_assos,
    }