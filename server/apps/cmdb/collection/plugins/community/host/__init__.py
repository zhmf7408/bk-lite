"""Host collection plugins."""

from apps.cmdb.collection.plugins.community.host.host import HostCollectionPlugin
from apps.cmdb.collection.plugins.community.host.physical_server import PhysicalServerCollectionPlugin

__all__ = ["HostCollectionPlugin", "PhysicalServerCollectionPlugin"]