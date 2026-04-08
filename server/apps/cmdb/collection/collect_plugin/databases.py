# -- coding: utf-8 --
# @File: databases.py
# @Time: 2025/11/12 14:18
# @Author: windyzhao
from apps.cmdb.collection.plugins import get_collection_plugin
from apps.cmdb.collection.plugins.base import bind_collection_mapping
from apps.cmdb.collection.plugins.community.db.base import BaseDBCollectionPlugin
from apps.cmdb.constants.constants import CollectPluginTypes


class DBCollectCollectMetrics(BaseDBCollectionPlugin):
    """兼容旧入口，实际定义统一走 DB 插件注册中心。"""

    def get_delegate_plugin(self):
        return get_collection_plugin(CollectPluginTypes.DB, self.model_id)

    @property
    def _metrics(self):
        plugin_cls = self.get_delegate_plugin()
        metric_names = getattr(plugin_cls, "metric_names", ())
        if not metric_names:
            raise AssertionError(f"{plugin_cls.__name__} needs metric_names")
        return list(metric_names)

    @property
    def model_field_mapping(self):
        plugin_cls = self.get_delegate_plugin()
        field_mapping = bind_collection_mapping(self, getattr(plugin_cls, "field_mapping", {}))
        return {self.model_id: field_mapping}
