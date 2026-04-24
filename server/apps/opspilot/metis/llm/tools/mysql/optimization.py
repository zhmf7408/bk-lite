"""MySQL优化建议工具"""

from collections import defaultdict

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
def check_unused_indexes(
    instance_name: str = None,
    instance_id: str = None,
    database: str = None,
    config: RunnableConfig = None,
) -> str:
    """检查未使用的索引。通过 performance_schema 分析从未被使用过的索引，帮助清理冗余索引以减少写入开销。"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            query = """
                SELECT OBJECT_SCHEMA, OBJECT_NAME AS TABLE_NAME, INDEX_NAME
                FROM performance_schema.table_io_waits_summary_by_index_usage
                WHERE INDEX_NAME IS NOT NULL
                  AND COUNT_STAR = 0
                  AND INDEX_NAME != 'PRIMARY'
            """
            params = None
            if database:
                query += " AND OBJECT_SCHEMA = %s"
                params = (database,)
            query += " ORDER BY OBJECT_SCHEMA, OBJECT_NAME"
            rows = execute_readonly_query(conn, query, params)
            return {
                "unused_indexes": rows,
                "total_count": len(rows),
                "recommendation": "建议删除未使用的索引以减少写入时的维护开销" if rows else "未发现未使用的索引",
            }
        except Error as e:
            if "performance_schema" in str(e).lower():
                return {"error": "performance_schema 不可用，请确认已启用 performance_schema"}
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def recommend_index_optimization(
    instance_name: str = None,
    instance_id: str = None,
    database: str = None,
    config: RunnableConfig = None,
) -> str:
    """分析并推荐索引优化方案。检测冗余索引（某索引是另一索引的前缀）和重复索引（相同列、相同顺序），给出优化建议。"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            query = """
                SELECT TABLE_SCHEMA, TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX, COLUMN_NAME
                FROM information_schema.STATISTICS
                WHERE NON_UNIQUE = 1
            """
            params = None
            if database:
                query += " AND TABLE_SCHEMA = %s"
                params = (database,)
            query += " ORDER BY TABLE_SCHEMA, TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX"
            rows = execute_readonly_query(conn, query, params)

            # Group columns by (schema, table, index)
            index_columns = defaultdict(list)
            for row in rows:
                key = (row["TABLE_SCHEMA"], row["TABLE_NAME"], row["INDEX_NAME"])
                index_columns[key].append(row["COLUMN_NAME"])

            # Group indexes by (schema, table)
            table_indexes = defaultdict(dict)
            for (schema, table, index), columns in index_columns.items():
                table_indexes[(schema, table)][index] = columns

            recommendations = []

            for (schema, table), indexes in table_indexes.items():
                index_names = list(indexes.keys())
                for i, idx_a in enumerate(index_names):
                    cols_a = indexes[idx_a]
                    for j, idx_b in enumerate(index_names):
                        if i == j:
                            continue
                        cols_b = indexes[idx_b]
                        # Duplicate: same columns in same order
                        if cols_a == cols_b:
                            if i < j:
                                recommendations.append(
                                    {
                                        "type": "duplicate",
                                        "schema": schema,
                                        "table": table,
                                        "index": idx_a,
                                        "duplicate_of": idx_b,
                                        "columns": cols_a,
                                        "suggestion": f"索引 {idx_a} 与 {idx_b} 完全重复，建议删除其中一个",
                                    }
                                )
                        # Redundant: cols_a is a prefix of cols_b
                        elif len(cols_a) < len(cols_b) and cols_b[: len(cols_a)] == cols_a:
                            recommendations.append(
                                {
                                    "type": "redundant",
                                    "schema": schema,
                                    "table": table,
                                    "index": idx_a,
                                    "covered_by": idx_b,
                                    "index_columns": cols_a,
                                    "covering_columns": cols_b,
                                    "suggestion": f"索引 {idx_a} 是 {idx_b} 的前缀，可考虑删除 {idx_a}",
                                }
                            )

            return {
                "recommendations": recommendations,
                "total_count": len(recommendations),
                "summary": f"发现 {len(recommendations)} 个可优化的索引" if recommendations else "未发现冗余或重复索引",
            }
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def check_table_fragmentation(
    instance_name: str = None,
    instance_id: str = None,
    database: str = None,
    config: RunnableConfig = None,
) -> str:
    """检查表碎片化情况。分析各表的数据碎片率，对碎片率超过20%的表建议执行 OPTIMIZE TABLE。"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            query = """
                SELECT
                    TABLE_NAME,
                    ENGINE,
                    TABLE_ROWS,
                    DATA_LENGTH,
                    INDEX_LENGTH,
                    DATA_FREE,
                    ROUND((DATA_FREE / (DATA_LENGTH + INDEX_LENGTH)) * 100, 2) AS frag_percent
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s
                  AND DATA_FREE > 0
                  AND DATA_LENGTH + INDEX_LENGTH > 0
                ORDER BY DATA_FREE DESC
            """
            rows = execute_readonly_query(conn, query, (database or "mysql",))

            tables = []
            high_frag = []
            for row in rows:
                entry = {
                    "table_name": row["TABLE_NAME"],
                    "engine": row["ENGINE"],
                    "table_rows": row["TABLE_ROWS"],
                    "data_length": format_size(row["DATA_LENGTH"]),
                    "index_length": format_size(row["INDEX_LENGTH"]),
                    "data_free": format_size(row["DATA_FREE"]),
                    "frag_percent": float(row["frag_percent"] or 0),
                }
                tables.append(entry)
                if entry["frag_percent"] > 20:
                    high_frag.append(entry["table_name"])

            return {
                "tables": tables,
                "total_count": len(tables),
                "high_fragmentation_tables": high_frag,
                "recommendation": (f"以下表碎片率超过20%，建议执行 OPTIMIZE TABLE: {', '.join(high_frag)}" if high_frag else "未发现严重碎片化的表"),
            }
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def check_configuration_tuning(
    instance_name: str = None,
    instance_id: str = None,
    config: RunnableConfig = None,
) -> str:
    """检查MySQL关键配置参数并提供调优建议。涵盖 innodb_buffer_pool_size、max_connections、innodb_log_file_size 等核心参数。"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            # Fetch variables
            var_rows = execute_readonly_query(conn, "SHOW GLOBAL VARIABLES")
            variables = {row["Variable_name"]: row["Value"] for row in var_rows}

            # Fetch status
            status_rows = execute_readonly_query(conn, "SHOW GLOBAL STATUS")
            status = {row["Variable_name"]: row["Value"] for row in status_rows}

            recommendations = []

            # innodb_buffer_pool_size
            bp_size = int(variables.get("innodb_buffer_pool_size", 0))
            recommendations.append(
                {
                    "variable": "innodb_buffer_pool_size",
                    "current_value": format_size(bp_size),
                    "advice": "建议设置为可用物理内存的70%-80%，当前值请结合服务器总内存评估",
                }
            )

            # max_connections vs Max_used_connections
            max_conn = int(variables.get("max_connections", 0))
            max_used = int(status.get("Max_used_connections", 0))
            usage_pct = calculate_percentage(max_used, max_conn) if max_conn else 0
            recommendations.append(
                {
                    "variable": "max_connections",
                    "current_value": max_conn,
                    "max_used_connections": max_used,
                    "usage_percent": usage_pct,
                    "advice": ("最大连接数使用率超过85%，建议适当增大 max_connections" if usage_pct > 85 else "连接数使用率正常"),
                }
            )

            # innodb_log_file_size
            log_file_size = int(variables.get("innodb_log_file_size", 0))
            recommendations.append(
                {
                    "variable": "innodb_log_file_size",
                    "current_value": format_size(log_file_size),
                    "advice": "写入密集型负载建议设置为256M-2G；过小会导致频繁checkpoint，过大会延长崩溃恢复时间",
                }
            )

            # innodb_flush_log_at_trx_commit
            flush_val = variables.get("innodb_flush_log_at_trx_commit", "1")
            recommendations.append(
                {
                    "variable": "innodb_flush_log_at_trx_commit",
                    "current_value": flush_val,
                    "advice": ("值为1时数据最安全但性能最低；值为2时性能较好但操作系统崩溃可能丢失1秒数据；值为0时性能最佳但风险最高"),
                }
            )

            # query_cache_type / query_cache_size (deprecated in 8.0)
            qc_type = variables.get("query_cache_type", None)
            qc_size = variables.get("query_cache_size", None)
            if qc_type is not None:
                recommendations.append(
                    {
                        "variable": "query_cache_type / query_cache_size",
                        "current_value": f"type={qc_type}, size={format_size(int(qc_size or 0))}",
                        "advice": "Query Cache 在 MySQL 8.0 已移除。如仍在使用旧版本，高并发下建议关闭以避免锁竞争",
                    }
                )

            # tmp_table_size / max_heap_table_size
            tmp_table_size = int(variables.get("tmp_table_size", 0))
            max_heap = int(variables.get("max_heap_table_size", 0))
            created_tmp_disk = int(status.get("Created_tmp_disk_tables", 0))
            created_tmp_total = int(status.get("Created_tmp_tables", 0))
            disk_pct = calculate_percentage(created_tmp_disk, created_tmp_total) if created_tmp_total else 0
            recommendations.append(
                {
                    "variable": "tmp_table_size / max_heap_table_size",
                    "tmp_table_size": format_size(tmp_table_size),
                    "max_heap_table_size": format_size(max_heap),
                    "created_tmp_disk_tables": created_tmp_disk,
                    "created_tmp_tables_total": created_tmp_total,
                    "disk_tmp_table_percent": disk_pct,
                    "advice": (
                        f"磁盘临时表比例为{disk_pct}%，较高。建议增大 tmp_table_size 和 max_heap_table_size，或优化产生大临时表的查询"
                        if disk_pct > 25
                        else "磁盘临时表比例正常"
                    ),
                }
            )

            return {"recommendations": recommendations}
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))
