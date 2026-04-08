from apps.cmdb.collection.collect_plugin.middleware import MiddlewareCollectMetrics
from apps.cmdb.collection.plugins.community.middleware.base import BaseMiddlewareCollectionPlugin


class JettyCollectionPlugin(BaseMiddlewareCollectionPlugin):
    supported_model_id = "jetty"
    metric_names = ("jetty_info_gauge",)
    field_mapping = {
        "inst_name": MiddlewareCollectMetrics.get_inst_name,
        "ip_addr": "ip_addr",
        "port": "port",
        "version": "version",
        "jetty_home": "jetty_home",
        "java_version": "java_version",
        "monitored_dir": "monitored_dir",
        "bin_path": "bin_path",
        "java_vendor": "java_vendor",
        "war_name": "war_name",
        "jvm_para": "jvm_para",
        "max_threads": "max_threads",
        "assos": MiddlewareCollectMetrics.get__host_assos,
    }