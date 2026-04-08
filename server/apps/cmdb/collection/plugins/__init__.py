from apps.cmdb.collection.plugins.registry import CollectionPluginRegistry


def get_collection_plugin(task_type: str, model_id: str):
    return CollectionPluginRegistry.get_plugin(task_type, model_id)