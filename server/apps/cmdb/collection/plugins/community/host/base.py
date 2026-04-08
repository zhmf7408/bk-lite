from apps.cmdb.collection.collect_plugin.host import HostCollectMetrics
from apps.cmdb.collection.plugins.base import AutoRegisterCollectionPluginMixin, bind_collection_mapping
from apps.cmdb.constants.constants import CollectPluginTypes


class BaseHostCollectionPlugin(AutoRegisterCollectionPluginMixin, HostCollectMetrics):
    supported_task_type = CollectPluginTypes.HOST
    plugin_source = "community"
    priority = 10
    metric_names = ()
    field_mapping = {}
    related_field_mappings = {}

    @property
    def _metrics(self):
        return list(self.metric_names)

    @property
    def model_field_mapping(self):
        mappings = {self.model_id: bind_collection_mapping(self, self.field_mapping)}
        for model_id, mapping in self.related_field_mappings.items():
            mappings[model_id] = bind_collection_mapping(self, mapping)
        return mappings