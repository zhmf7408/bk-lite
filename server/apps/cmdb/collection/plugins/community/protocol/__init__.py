"""Protocol collection plugins."""

from apps.cmdb.collection.plugins.community.protocol.mssql import MssqlCollectionPlugin
from apps.cmdb.collection.plugins.community.protocol.mysql import MysqlCollectionPlugin
from apps.cmdb.collection.plugins.community.protocol.oracle import OracleCollectionPlugin
from apps.cmdb.collection.plugins.community.protocol.postgresql import PostgresqlCollectionPlugin

__all__ = [
	"MysqlCollectionPlugin",
	"PostgresqlCollectionPlugin",
	"OracleCollectionPlugin",
	"MssqlCollectionPlugin",
]