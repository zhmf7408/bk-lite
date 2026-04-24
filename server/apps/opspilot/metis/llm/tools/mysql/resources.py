"""MySQL基础资源查询工具"""

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from mysql.connector import Error

from apps.opspilot.metis.llm.tools.common.credentials import execute_with_credentials
from apps.opspilot.metis.llm.tools.mysql.connection import (
    build_mysql_normalized_from_runnable,
    get_mysql_connection_from_item,
)
from apps.opspilot.metis.llm.tools.mysql.utils import (
    calculate_percentage,
    execute_readonly_query,
    format_size,
    safe_json_dumps,
)


@tool()
def get_current_database_info(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """获取当前MySQL实例的基本信息，包括版本、主机名、端口、数据目录、字符集、排序规则、默认存储引擎和运行时间"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            info_query = """
            SELECT
                VERSION() AS version,
                @@hostname AS hostname,
                @@port AS port,
                @@datadir AS datadir,
                @@character_set_server AS character_set_server,
                @@collation_server AS collation_server,
                @@default_storage_engine AS default_storage_engine
            """
            result = execute_readonly_query(conn, info_query)[0]

            uptime_query = """
            SELECT VARIABLE_VALUE AS uptime_seconds
            FROM performance_schema.global_status
            WHERE VARIABLE_NAME = 'Uptime'
            """
            try:
                uptime_result = execute_readonly_query(conn, uptime_query)
                uptime = uptime_result[0]["uptime_seconds"] if uptime_result else "unknown"
            except Error:
                uptime = "unknown"

            return {
                "version": result["version"],
                "hostname": result["hostname"],
                "port": result["port"],
                "datadir": result["datadir"],
                "character_set_server": result["character_set_server"],
                "collation_server": result["collation_server"],
                "default_storage_engine": result["default_storage_engine"],
                "uptime_seconds": uptime,
            }
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def list_mysql_databases(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """列出所有MySQL数据库及其大小信息"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            query = """
            SELECT
                s.SCHEMA_NAME,
                s.DEFAULT_CHARACTER_SET_NAME,
                s.DEFAULT_COLLATION_NAME,
                IFNULL(t.total_size, 0) AS size_bytes
            FROM information_schema.SCHEMATA s
            LEFT JOIN (
                SELECT
                    TABLE_SCHEMA,
                    SUM(DATA_LENGTH + INDEX_LENGTH) AS total_size
                FROM information_schema.TABLES
                GROUP BY TABLE_SCHEMA
            ) t ON s.SCHEMA_NAME = t.TABLE_SCHEMA
            ORDER BY size_bytes DESC
            """
            results = execute_readonly_query(conn, query)

            databases = []
            for row in results:
                databases.append(
                    {
                        "schema_name": row["SCHEMA_NAME"],
                        "character_set": row["DEFAULT_CHARACTER_SET_NAME"],
                        "collation": row["DEFAULT_COLLATION_NAME"],
                        "size": format_size(row["size_bytes"]),
                        "size_bytes": row["size_bytes"],
                    }
                )

            return {"total_databases": len(databases), "databases": databases}
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def list_mysql_tables(database: str = None, instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """列出指定数据库中的所有表及其基本信息，包括引擎、行数、数据大小、索引大小和备注"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            db = database
            if not db:
                db_result = execute_readonly_query(conn, "SELECT DATABASE() AS current_db")
                db = db_result[0]["current_db"] if db_result and db_result[0]["current_db"] else None
                if not db:
                    return {"error": "未指定数据库且当前连接未选择数据库"}

            query = """
            SELECT
                TABLE_NAME,
                ENGINE,
                TABLE_ROWS,
                DATA_LENGTH,
                INDEX_LENGTH,
                TABLE_COMMENT
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY DATA_LENGTH + INDEX_LENGTH DESC
            """
            results = execute_readonly_query(conn, query, params=(db,))

            tables = []
            for row in results:
                data_len = row["DATA_LENGTH"] or 0
                index_len = row["INDEX_LENGTH"] or 0
                tables.append(
                    {
                        "table_name": row["TABLE_NAME"],
                        "engine": row["ENGINE"],
                        "table_rows": row["TABLE_ROWS"],
                        "data_size": format_size(data_len),
                        "index_size": format_size(index_len),
                        "total_size": format_size(data_len + index_len),
                        "table_comment": row["TABLE_COMMENT"],
                    }
                )

            return {"database": db, "total_tables": len(tables), "tables": tables}
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def list_mysql_indexes(
    table_name: str, database: str = None, instance_name: str = None, instance_id: str = None, config: RunnableConfig = None
) -> str:
    """列出指定表的所有索引信息，包括索引名、列名、是否唯一、顺序、索引类型和基数"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            db = database
            if not db:
                db_result = execute_readonly_query(conn, "SELECT DATABASE() AS current_db")
                db = db_result[0]["current_db"] if db_result and db_result[0]["current_db"] else None
                if not db:
                    return {"error": "未指定数据库且当前连接未选择数据库"}

            query = """
            SELECT
                INDEX_NAME,
                COLUMN_NAME,
                NON_UNIQUE,
                SEQ_IN_INDEX,
                INDEX_TYPE,
                CARDINALITY
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY INDEX_NAME, SEQ_IN_INDEX
            """
            results = execute_readonly_query(conn, query, params=(db, table_name))

            indexes = []
            for row in results:
                indexes.append(
                    {
                        "index_name": row["INDEX_NAME"],
                        "column_name": row["COLUMN_NAME"],
                        "non_unique": row["NON_UNIQUE"],
                        "seq_in_index": row["SEQ_IN_INDEX"],
                        "index_type": row["INDEX_TYPE"],
                        "cardinality": row["CARDINALITY"],
                    }
                )

            return {"database": db, "table": table_name, "total_indexes": len(indexes), "indexes": indexes}
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def list_mysql_schemas(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """列出所有MySQL Schema（数据库），包括名称、字符集和排序规则"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            query = """
            SELECT
                SCHEMA_NAME,
                DEFAULT_CHARACTER_SET_NAME,
                DEFAULT_COLLATION_NAME
            FROM information_schema.SCHEMATA
            ORDER BY SCHEMA_NAME
            """
            results = execute_readonly_query(conn, query)

            schemas = []
            for row in results:
                schemas.append(
                    {
                        "schema_name": row["SCHEMA_NAME"],
                        "character_set": row["DEFAULT_CHARACTER_SET_NAME"],
                        "collation": row["DEFAULT_COLLATION_NAME"],
                    }
                )

            return {"total_schemas": len(schemas), "schemas": schemas}
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def get_table_structure(
    table_name: str, database: str = None, instance_name: str = None, instance_id: str = None, config: RunnableConfig = None
) -> str:
    """获取指定表的完整结构，包括列定义、索引和约束信息"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            db = database
            if not db:
                db_result = execute_readonly_query(conn, "SELECT DATABASE() AS current_db")
                db = db_result[0]["current_db"] if db_result and db_result[0]["current_db"] else None
                if not db:
                    return {"error": "未指定数据库且当前连接未选择数据库"}

            # 列信息
            columns_query = """
            SELECT
                COLUMN_NAME,
                COLUMN_TYPE,
                IS_NULLABLE,
                COLUMN_KEY,
                COLUMN_DEFAULT,
                EXTRA,
                COLUMN_COMMENT
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
            """
            columns = execute_readonly_query(conn, columns_query, params=(db, table_name))

            # 索引信息
            indexes_query = """
            SELECT
                INDEX_NAME,
                COLUMN_NAME,
                NON_UNIQUE,
                SEQ_IN_INDEX,
                INDEX_TYPE
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY INDEX_NAME, SEQ_IN_INDEX
            """
            indexes = execute_readonly_query(conn, indexes_query, params=(db, table_name))

            # 约束信息
            constraints_query = """
            SELECT
                tc.CONSTRAINT_NAME,
                tc.CONSTRAINT_TYPE,
                kcu.COLUMN_NAME,
                kcu.REFERENCED_TABLE_NAME,
                kcu.REFERENCED_COLUMN_NAME
            FROM information_schema.TABLE_CONSTRAINTS tc
            JOIN information_schema.KEY_COLUMN_USAGE kcu
                ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                AND tc.TABLE_SCHEMA = kcu.TABLE_SCHEMA
                AND tc.TABLE_NAME = kcu.TABLE_NAME
            WHERE tc.TABLE_SCHEMA = %s AND tc.TABLE_NAME = %s
            ORDER BY tc.CONSTRAINT_TYPE, tc.CONSTRAINT_NAME, kcu.ORDINAL_POSITION
            """
            constraints = execute_readonly_query(conn, constraints_query, params=(db, table_name))

            return {
                "database": db,
                "table": table_name,
                "columns": columns,
                "indexes": indexes,
                "constraints": constraints,
            }
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def list_mysql_users(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """列出所有MySQL用户及其关键权限信息"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            query = """
            SELECT
                Host,
                User,
                Select_priv,
                Insert_priv,
                Update_priv,
                Delete_priv,
                Grant_priv,
                Super_priv
            FROM mysql.user
            ORDER BY User, Host
            """
            try:
                results = execute_readonly_query(conn, query)
            except Error:
                # 权限不足时回退到SHOW GRANTS查询当前用户
                fallback_query = "SELECT CURRENT_USER() AS current_user"
                current = execute_readonly_query(conn, fallback_query)
                return {
                    "error": "权限不足，无法查询mysql.user表",
                    "current_user": current[0]["current_user"] if current else "unknown",
                }

            users = []
            for row in results:
                users.append(
                    {
                        "host": row["Host"],
                        "user": row["User"],
                        "select_priv": row["Select_priv"],
                        "insert_priv": row["Insert_priv"],
                        "update_priv": row["Update_priv"],
                        "delete_priv": row["Delete_priv"],
                        "grant_priv": row["Grant_priv"],
                        "super_priv": row["Super_priv"],
                    }
                )

            return {"total_users": len(users), "users": users}
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def get_database_config(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """获取MySQL关键配置参数，包括缓冲池大小、最大连接数、查询缓存、日志文件大小、刷新方式、字符集、SQL模式等"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            target_variables = [
                "innodb_buffer_pool_size",
                "max_connections",
                "query_cache_size",
                "innodb_log_file_size",
                "innodb_flush_method",
                "character_set_server",
                "collation_server",
                "sql_mode",
                "wait_timeout",
                "max_allowed_packet",
            ]

            settings = {}
            for var in target_variables:
                try:
                    query = "SHOW GLOBAL VARIABLES LIKE %s"
                    result = execute_readonly_query(conn, query, params=(var,))
                    if result:
                        value = result[0].get("Value") or result[0].get("VALUE") or list(result[0].values())[1]
                        settings[var] = value
                    else:
                        settings[var] = None
                except Error:
                    settings[var] = None

            # 格式化字节类大小的配置项
            size_keys = ["innodb_buffer_pool_size", "query_cache_size", "innodb_log_file_size", "max_allowed_packet"]
            formatted = {}
            for key, value in settings.items():
                formatted[key] = {"value": value}
                if key in size_keys and value is not None:
                    try:
                        formatted[key]["display"] = format_size(int(value))
                    except (ValueError, TypeError):
                        pass

            return {"total_settings": len(formatted), "settings": formatted}
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))
