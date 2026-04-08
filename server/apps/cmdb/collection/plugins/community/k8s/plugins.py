from apps.cmdb.collection.collect_plugin.k8s import CollectK8sMetrics
from apps.cmdb.collection.plugins.base import AutoRegisterCollectionPluginMixin
from apps.cmdb.constants.constants import CollectPluginTypes


class K8sClusterCollectionPlugin(AutoRegisterCollectionPluginMixin, CollectK8sMetrics):
    supported_task_type = CollectPluginTypes.K8S
    supported_model_id = "k8s_cluster"
    plugin_source = "community"
    priority = 10