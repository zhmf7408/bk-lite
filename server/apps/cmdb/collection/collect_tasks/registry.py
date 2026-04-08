from apps.cmdb.collection.collect_tasks.base import BaseCollect
from apps.cmdb.collection.plugins import get_collection_plugin


class RegisteredCollect(BaseCollect):
    def get_collect_plugin(self):
        return get_collection_plugin(self.task.task_type, self.model_id)