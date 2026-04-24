import inspect

from apps.cmdb.collection.collect_plugin.base import CollectBase
from apps.cmdb.collection.plugins.registry import CollectionPluginRegistry


def _bind_collection_callable(instance, value):
    if inspect.ismethod(value):
        return value

    if not callable(value) or not hasattr(value, "__get__"):
        return value

    func_name = getattr(value, "__name__", "")
    if not func_name:
        return value

    for cls in instance.__class__.__mro__:
        descriptor = inspect.getattr_static(cls, func_name, None)
        if descriptor is None:
            continue
        if isinstance(descriptor, staticmethod):
            return value
        return value.__get__(instance, instance.__class__)

    return value


def bind_collection_mapping(instance, mapping):
    bound_mapping = {}
    for field, value in mapping.items():
        if isinstance(value, tuple):
            func, *rest = value
            func = _bind_collection_callable(instance, func)
            bound_mapping[field] = (func, *rest)
            continue

        if callable(value):
            bound_mapping[field] = _bind_collection_callable(instance, value)
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