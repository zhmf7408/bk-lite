from apps.cmdb.collection.collect_plugin.base import CollectBase
from apps.cmdb.collection.plugins.registry import CollectionPluginRegistry


def bind_collection_mapping(instance, mapping):
    bound_mapping = {}
    for field, value in mapping.items():
        if isinstance(value, tuple):
            func, *rest = value
            if callable(func) and hasattr(func, "__get__"):
                func = func.__get__(instance, instance.__class__)
            bound_mapping[field] = (func, *rest)
            continue

        if callable(value) and hasattr(value, "__get__"):
            bound_mapping[field] = value.__get__(instance, instance.__class__)
            continue

        bound_mapping[field] = value

    return bound_mapping


class AutoRegisterCollectionPluginMixin:
    supported_task_type = None
    supported_model_id = None
    plugin_source = "community"
    priority = 10

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls is AutoRegisterCollectionPluginMixin:
            return

        task_type = getattr(cls, "supported_task_type", None)
        model_id = getattr(cls, "supported_model_id", None)
        if task_type and model_id:
            CollectionPluginRegistry.register(cls)


class BaseCollectionPlugin(AutoRegisterCollectionPluginMixin, CollectBase):
    pass