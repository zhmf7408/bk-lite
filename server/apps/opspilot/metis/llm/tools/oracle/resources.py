"""Oracle基础资源查询工具"""

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
import oracledb

from apps.opspilot.metis.llm.tools.common.credentials import execute_with_credentials
from apps.opspilot.metis.llm.tools.oracle.connection import (
    build_oracle_normalized_from_runnable,
    get_oracle_connection_from_item,
)
from apps.opspilot.metis.llm.tools.oracle.utils import (
    calculate_percentage,
    execute_readonly_query,
    format_size,
    safe_json_dumps,
)


@tool()
def get_current_database_info(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """获取Oracle实例基本信息，包括数据库名、实例名、版本、状态、字符集和运行时间"""
    normalized = build_oracle_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_oracle_connection_from_item(item)
        try:
            db_query = """
            SELECT NAME, DB_UNIQUE_NAME, OPEN_MODE, LOG_MODE
            FROM v$database
            """
            db_result = execute_readonly_query(conn, db_query)
            db_info = db_result[0] if db_result else {}

            instance_query = """
            SELECT INSTANCE_NAME, HOST_NAME, STATUS, STARTUP_TIME
            FROM v$instance
            """
            instance_result = execute_readonly_query(conn, instance_query)
            instance_info = instance_result[0] if instance_result else {}

            version_query = """
            SELECT BANNER FROM v$version WHERE ROWNUM = 1
            """
            version_result = execute_readonly_query(conn, version_query)
            version = version_result[0]["BANNER"] if version_result else "unknown"

            return {
                "database_name": db_info.get("NAME"),
                "db_unique_name": db_info.get("DB_UNIQUE_NAME"),
                "open_mode": db_info.get("OPEN_MODE"),
                "log_mode": db_info.get("LOG_MODE"),
                "instance_name": instance_info.get("INSTANCE_NAME"),
                "host_name": instance_info.get("HOST_NAME"),
                "status": instance_info.get("STATUS"),
                "startup_time": str(instance_info.get("STARTUP_TIME", "")),
                "version": version,
            }
        except oracledb.Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def list_oracle_tablespaces(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """列出所有Oracle表空间及其使用情况"""
    normalized = build_oracle_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_oracle_connection_from_item(item)
        try:
            query = """
            SELECT
                t.TABLESPACE_NAME,
                t.STATUS,
                t.CONTENTS,
                t.LOGGING,
                NVL(d.total_bytes, 0) AS total_bytes,
                NVL(f.free_bytes, 0) AS free_bytes
            FROM dba_tablespaces t
            LEFT JOIN (
                SELECT TABLESPACE_NAME, SUM(BYTES) AS total_bytes
                FROM dba_data_files
                GROUP BY TABLESPACE_NAME
            ) d ON t.TABLESPACE_NAME = d.TABLESPACE_NAME
            LEFT JOIN (
                SELECT TABLESPACE_NAME, SUM(BYTES) AS free_bytes
                FROM dba_free_space
                GROUP BY TABLESPACE_NAME
            ) f ON t.TABLESPACE_NAME = f.TABLESPACE_NAME
            ORDER BY total_bytes DESC
            """
            results = execute_readonly_query(conn, query)

            tablespaces = []
            for row in results:
                total = row["TOTAL_BYTES"] or 0
                free = row["FREE_BYTES"] or 0
                used = total - free
                tablespaces.append(
                    {
                        "tablespace_name": row["TABLESPACE_NAME"],
                        "status": row["STATUS"],
                        "contents": row["CONTENTS"],
                        "logging": row["LOGGING"],
                        "total_size": format_size(total),
                        "used_size": format_size(used),
                        "free_size": format_size(free),
                        "usage_percentage": calculate_percentage(used, total),
                    }
                )

            return {"total_tablespaces": len(tablespaces), "tablespaces": tablespaces}
        except oracledb.Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def list_oracle_tables(schema: str = None, instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """列出指定Schema或当前用户的表及行数、大小信息"""
    normalized = build_oracle_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_oracle_connection_from_item(item)
        try:
            if schema:
                query = """
                SELECT
                    t.OWNER,
                    t.TABLE_NAME,
                    t.NUM_ROWS,
                    t.LAST_ANALYZED,
                    NVL(s.BYTES, 0) AS size_bytes
                FROM all_tables t
                LEFT JOIN all_segments s
                    ON t.OWNER = s.OWNER AND t.TABLE_NAME = s.SEGMENT_NAME AND s.SEGMENT_TYPE = 'TABLE'
                WHERE t.OWNER = UPPER(:schema)
                ORDER BY size_bytes DESC
                """
                results = execute_readonly_query(conn, query, params={"schema": schema})
            else:
                query = """
                SELECT
                    USER AS OWNER,
                    t.TABLE_NAME,
                    t.NUM_ROWS,
                    t.LAST_ANALYZED,
                    NVL(s.BYTES, 0) AS size_bytes
                FROM user_tables t
                LEFT JOIN user_segments s
                    ON t.TABLE_NAME = s.SEGMENT_NAME AND s.SEGMENT_TYPE = 'TABLE'
                ORDER BY size_bytes DESC
                """
                results = execute_readonly_query(conn, query)

            tables = []
            for row in results:
                size_bytes = row["SIZE_BYTES"] or 0
                tables.append(
                    {
                        "owner": row["OWNER"],
                        "table_name": row["TABLE_NAME"],
                        "num_rows": row["NUM_ROWS"],
                        "size": format_size(size_bytes),
                        "size_bytes": size_bytes,
                        "last_analyzed": str(row.get("LAST_ANALYZED", "")),
                    }
                )

            return {"schema": schema or "current_user", "total_tables": len(tables), "tables": tables}
        except oracledb.Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def list_oracle_indexes(
    table_name: str = None, schema: str = None, instance_name: str = None, instance_id: str = None, config: RunnableConfig = None
) -> str:
    """列出指定表或Schema的索引信息"""
    normalized = build_oracle_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_oracle_connection_from_item(item)
        try:
            conditions = []
            params = {}

            if schema:
                conditions.append("i.OWNER = UPPER(:schema)")
                params["schema"] = schema
            if table_name:
                conditions.append("i.TABLE_NAME = UPPER(:table_name)")
                params["table_name"] = table_name

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

            query = f"""
            SELECT
                i.OWNER,
                i.INDEX_NAME,
                i.TABLE_NAME,
                i.INDEX_TYPE,
                i.UNIQUENESS,
                i.STATUS,
                i.NUM_ROWS,
                c.COLUMN_NAME,
                c.COLUMN_POSITION
            FROM all_indexes i
            JOIN all_ind_columns c
                ON i.OWNER = c.INDEX_OWNER AND i.INDEX_NAME = c.INDEX_NAME
            {where_clause}
            ORDER BY i.OWNER, i.TABLE_NAME, i.INDEX_NAME, c.COLUMN_POSITION
            """
            results = execute_readonly_query(conn, query, params=params if params else None)

            indexes = []
            for row in results:
                indexes.append(
                    {
                        "owner": row["OWNER"],
                        "index_name": row["INDEX_NAME"],
                        "table_name": row["TABLE_NAME"],
                        "index_type": row["INDEX_TYPE"],
                        "uniqueness": row["UNIQUENESS"],
                        "status": row["STATUS"],
                        "num_rows": row["NUM_ROWS"],
                        "column_name": row["COLUMN_NAME"],
                        "column_position": row["COLUMN_POSITION"],
                    }
                )

            return {"total_indexes": len(indexes), "indexes": indexes}
        except oracledb.Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def get_table_structure(
    table_name: str, schema: str = None, instance_name: str = None, instance_id: str = None, config: RunnableConfig = None
) -> str:
    """获取Oracle表的详细结构，包括列定义和约束"""
    normalized = build_oracle_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_oracle_connection_from_item(item)
        try:
            if schema:
                columns_query = """
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    DATA_LENGTH,
                    DATA_PRECISION,
                    DATA_SCALE,
                    NULLABLE,
                    DATA_DEFAULT,
                    COLUMN_ID
                FROM all_tab_columns
                WHERE OWNER = UPPER(:schema) AND TABLE_NAME = UPPER(:table_name)
                ORDER BY COLUMN_ID
                """
                columns = execute_readonly_query(conn, columns_query, params={"schema": schema, "table_name": table_name})

                constraints_query = """
                SELECT
                    c.CONSTRAINT_NAME,
                    c.CONSTRAINT_TYPE,
                    c.STATUS,
                    cc.COLUMN_NAME,
                    cc.POSITION
                FROM all_constraints c
                JOIN all_cons_columns cc
                    ON c.OWNER = cc.OWNER AND c.CONSTRAINT_NAME = cc.CONSTRAINT_NAME
                WHERE c.OWNER = UPPER(:schema) AND c.TABLE_NAME = UPPER(:table_name)
                ORDER BY c.CONSTRAINT_TYPE, c.CONSTRAINT_NAME, cc.POSITION
                """
                constraints = execute_readonly_query(conn, constraints_query, params={"schema": schema, "table_name": table_name})
            else:
                columns_query = """
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    DATA_LENGTH,
                    DATA_PRECISION,
                    DATA_SCALE,
                    NULLABLE,
                    DATA_DEFAULT,
                    COLUMN_ID
                FROM user_tab_columns
                WHERE TABLE_NAME = UPPER(:table_name)
                ORDER BY COLUMN_ID
                """
                columns = execute_readonly_query(conn, columns_query, params={"table_name": table_name})

                constraints_query = """
                SELECT
                    c.CONSTRAINT_NAME,
                    c.CONSTRAINT_TYPE,
                    c.STATUS,
                    cc.COLUMN_NAME,
                    cc.POSITION
                FROM user_constraints c
                JOIN user_cons_columns cc
                    ON c.CONSTRAINT_NAME = cc.CONSTRAINT_NAME
                WHERE c.TABLE_NAME = UPPER(:table_name)
                ORDER BY c.CONSTRAINT_TYPE, c.CONSTRAINT_NAME, cc.POSITION
                """
                constraints = execute_readonly_query(conn, constraints_query, params={"table_name": table_name})

            column_list = []
            for row in columns:
                column_list.append(
                    {
                        "column_name": row["COLUMN_NAME"],
                        "data_type": row["DATA_TYPE"],
                        "data_length": row["DATA_LENGTH"],
                        "data_precision": row["DATA_PRECISION"],
                        "data_scale": row["DATA_SCALE"],
                        "nullable": row["NULLABLE"],
                        "data_default": str(row.get("DATA_DEFAULT", "")) if row.get("DATA_DEFAULT") else None,
                        "column_id": row["COLUMN_ID"],
                    }
                )

            constraint_list = []
            for row in constraints:
                constraint_list.append(
                    {
                        "constraint_name": row["CONSTRAINT_NAME"],
                        "constraint_type": row["CONSTRAINT_TYPE"],
                        "status": row["STATUS"],
                        "column_name": row["COLUMN_NAME"],
                        "position": row["POSITION"],
                    }
                )

            return {
                "schema": schema or "current_user",
                "table": table_name,
                "columns": column_list,
                "constraints": constraint_list,
            }
        except oracledb.Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def list_oracle_users(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """列出Oracle数据库用户及其状态和角色"""
    normalized = build_oracle_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_oracle_connection_from_item(item)
        try:
            users_query = """
            SELECT
                USERNAME,
                ACCOUNT_STATUS,
                DEFAULT_TABLESPACE,
                CREATED
            FROM dba_users
            ORDER BY USERNAME
            """
            try:
                users_result = execute_readonly_query(conn, users_query)
            except oracledb.Error:
                fallback_query = "SELECT USER AS USERNAME FROM DUAL"
                current = execute_readonly_query(conn, fallback_query)
                return {
                    "error": "权限不足，无法查询dba_users视图",
                    "current_user": current[0]["USERNAME"] if current else "unknown",
                }

            roles_query = """
            SELECT GRANTEE, GRANTED_ROLE
            FROM dba_role_privs
            ORDER BY GRANTEE, GRANTED_ROLE
            """
            try:
                roles_result = execute_readonly_query(conn, roles_query)
            except oracledb.Error:
                roles_result = []

            role_map = {}
            for row in roles_result:
                grantee = row["GRANTEE"]
                if grantee not in role_map:
                    role_map[grantee] = []
                role_map[grantee].append(row["GRANTED_ROLE"])

            users = []
            for row in users_result:
                username = row["USERNAME"]
                users.append(
                    {
                        "username": username,
                        "account_status": row["ACCOUNT_STATUS"],
                        "default_tablespace": row["DEFAULT_TABLESPACE"],
                        "created": str(row.get("CREATED", "")),
                        "granted_roles": role_map.get(username, []),
                    }
                )

            return {"total_users": len(users), "users": users}
        except oracledb.Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def get_database_config(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """获取Oracle关键配置参数"""
    normalized = build_oracle_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_oracle_connection_from_item(item)
        try:
            target_params = [
                "db_block_size",
                "db_cache_size",
                "shared_pool_size",
                "pga_aggregate_target",
                "sga_target",
                "sga_max_size",
                "memory_target",
                "memory_max_target",
                "processes",
                "sessions",
                "open_cursors",
                "cursor_sharing",
                "optimizer_mode",
                "undo_tablespace",
                "undo_retention",
                "log_buffer",
                "db_recovery_file_dest_size",
                "audit_trail",
            ]

            placeholders = ", ".join([f":{i}" for i in range(len(target_params))])
            query = f"""
            SELECT NAME, VALUE, DISPLAY_VALUE, DESCRIPTION
            FROM v$parameter
            WHERE LOWER(NAME) IN ({placeholders})
            ORDER BY NAME
            """
            params = {str(i): p for i, p in enumerate(target_params)}
            results = execute_readonly_query(conn, query, params=params)

            size_keys = {
                "db_block_size",
                "db_cache_size",
                "shared_pool_size",
                "pga_aggregate_target",
                "sga_target",
                "sga_max_size",
                "memory_target",
                "memory_max_target",
                "log_buffer",
                "db_recovery_file_dest_size",
            }

            settings = {}
            for row in results:
                name = row["NAME"]
                value = row["VALUE"]
                entry = {
                    "value": value,
                    "display_value": row.get("DISPLAY_VALUE"),
                    "description": row.get("DESCRIPTION"),
                }
                if name in size_keys and value is not None:
                    try:
                        entry["formatted_size"] = format_size(int(value))
                    except (ValueError, TypeError):
                        pass
                settings[name] = entry

            return {"total_settings": len(settings), "settings": settings}
        except oracledb.Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))
