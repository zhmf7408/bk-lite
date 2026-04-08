"""Middleware collection plugins."""

from apps.cmdb.collection.plugins.community.middleware.activemq import ActivemqCollectionPlugin
from apps.cmdb.collection.plugins.community.middleware.apache import ApacheCollectionPlugin
from apps.cmdb.collection.plugins.community.middleware.consul import ConsulCollectionPlugin
from apps.cmdb.collection.plugins.community.middleware.docker import DockerCollectionPlugin
from apps.cmdb.collection.plugins.community.middleware.etcd import EtcdCollectionPlugin
from apps.cmdb.collection.plugins.community.middleware.jetty import JettyCollectionPlugin
from apps.cmdb.collection.plugins.community.middleware.kafka import KafkaCollectionPlugin
from apps.cmdb.collection.plugins.community.middleware.keepalived import KeepalivedCollectionPlugin
from apps.cmdb.collection.plugins.community.middleware.nginx import NginxCollectionPlugin
from apps.cmdb.collection.plugins.community.middleware.rabbitmq import RabbitmqCollectionPlugin
from apps.cmdb.collection.plugins.community.middleware.tomcat import TomcatCollectionPlugin
from apps.cmdb.collection.plugins.community.middleware.tongweb import TongwebCollectionPlugin
from apps.cmdb.collection.plugins.community.middleware.weblogic import WeblogicCollectionPlugin
from apps.cmdb.collection.plugins.community.middleware.zookeeper import ZookeeperCollectionPlugin

__all__ = [
	"NginxCollectionPlugin",
	"ZookeeperCollectionPlugin",
	"KafkaCollectionPlugin",
	"EtcdCollectionPlugin",
	"RabbitmqCollectionPlugin",
	"TomcatCollectionPlugin",
	"ConsulCollectionPlugin",
	"DockerCollectionPlugin",
	"ApacheCollectionPlugin",
	"ActivemqCollectionPlugin",
	"WeblogicCollectionPlugin",
	"KeepalivedCollectionPlugin",
	"TongwebCollectionPlugin",
	"JettyCollectionPlugin",
]