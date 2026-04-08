from apps.cmdb.collection.collect_plugin.protocol import ProtocolCollectMetrics
from apps.cmdb.collection.plugins.base import AutoRegisterCollectionPluginMixin, bind_collection_mapping
from apps.cmdb.constants.constants import CollectPluginTypes


class BaseProtocolCollectionPlugin(AutoRegisterCollectionPluginMixin, ProtocolCollectMetrics):
    supported_task_type = CollectPluginTypes.PROTOCOL
    plugin_source = "community"
    priority = 10
    metric_names = ()
    field_mapping = {}

    @property
    def _metrics(self):
        return list(self.metric_names)

    @property
    def model_field_mapping(self):
        return {self.model_id: bind_collection_mapping(self, self.field_mapping)}