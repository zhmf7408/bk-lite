from apps.cmdb.collection.collect_plugin.middleware import MiddlewareCollectMetrics
from apps.cmdb.collection.plugins.community.middleware.base import BaseMiddlewareCollectionPlugin


class ApacheCollectionPlugin(BaseMiddlewareCollectionPlugin):
    supported_model_id = "apache"
    metric_names = ("apache_info_gauge",)
    field_mapping = {
        "inst_name": MiddlewareCollectMetrics.get_inst_name,
        "ip_addr": "ip_addr",
        "port": "port",
        "version": "version",
        "httpd_path": "httpd_path",
        "httpd_conf_path": "httpd_conf_path",
        "doc_root": "doc_root",
        "error_log": "error_log",
        "custom_Log": "custom_Log",
        "include": "include",
        "assos": MiddlewareCollectMetrics.get__host_assos,
    }