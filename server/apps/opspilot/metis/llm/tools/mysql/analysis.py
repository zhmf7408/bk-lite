"""MySQL分析工具"""

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
def analyze_buffer_pool_usage(
    instance_name: str = None,
    instance_id: str = None,
    config: RunnableConfig = None,
) -> str:
    """分析InnoDB缓冲池使用情况。包括命中率、脏页比例、空闲页比例和页面利用率等关键指标。"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            rows = execute_readonly_query(conn, "SHOW GLOBAL STATUS")
            status = {row["Variable_name"]: row["Value"] for row in rows}

            pages_total = int(status.get("Innodb_buffer_pool_pages_total", 0))
            pages_data = int(status.get("Innodb_buffer_pool_pages_data", 0))
            pages_free = int(status.get("Innodb_buffer_pool_pages_free", 0))
            pages_dirty = int(status.get("Innodb_buffer_pool_pages_dirty", 0))
            pages_flushed = int(status.get("Innodb_buffer_pool_pages_flushed", 0))
            read_requests = int(status.get("Innodb_buffer_pool_read_requests", 0))
            reads = int(status.get("Innodb_buffer_pool_reads", 0))

            hit_ratio = calculate_percentage(read_requests - reads, read_requests) if read_requests else 0
            dirty_ratio = calculate_percentage(pages_dirty, pages_total) if pages_total else 0
            free_ratio = calculate_percentage(pages_free, pages_total) if pages_total else 0
            utilization = calculate_percentage(pages_data, pages_total) if pages_total else 0

            return {
                "pages_total": pages_total,
                "pages_data": pages_data,
                "pages_free": pages_free,
                "pages_dirty": pages_dirty,
                "pages_flushed": pages_flushed,
                "read_requests": read_requests,
                "disk_reads": reads,
                "hit_ratio_percent": hit_ratio,
                "dirty_ratio_percent": dirty_ratio,
                "free_ratio_percent": free_ratio,
                "utilization_percent": utilization,
                "recommendation": ("缓冲池命中率低于95%，建议增大 innodb_buffer_pool_size" if hit_ratio < 95 else "缓冲池命中率良好"),
            }
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def analyze_query_patterns(
    instance_name: str = None,
    instance_id: str = None,
    config: RunnableConfig = None,
) -> str:
    """分析查询模式。从 performance_schema 获取高频查询摘要，识别全表扫描和全连接查询，帮助定位性能瓶颈。"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            query = """
                SELECT
                    DIGEST_TEXT,
                    SCHEMA_NAME,
                    COUNT_STAR,
                    SUM_TIMER_WAIT,
                    AVG_TIMER_WAIT,
                    SUM_ROWS_EXAMINED,
                    SUM_ROWS_SENT,
                    SUM_SELECT_FULL_JOIN,
                    SUM_SELECT_SCAN,
                    SUM_SORT_MERGE_PASSES
                FROM performance_schema.events_statements_summary_by_digest
                WHERE DIGEST_TEXT IS NOT NULL
                ORDER BY COUNT_STAR DESC
                LIMIT 30
            """
            rows = execute_readonly_query(conn, query)

            full_table_scans = []
            full_joins = []
            patterns = []

            for row in rows:
                entry = {
                    "digest_text": row["DIGEST_TEXT"],
                    "schema_name": row["SCHEMA_NAME"],
                    "exec_count": row["COUNT_STAR"],
                    "total_time_ps": row["SUM_TIMER_WAIT"],
                    "avg_time_ps": row["AVG_TIMER_WAIT"],
                    "rows_examined": row["SUM_ROWS_EXAMINED"],
                    "rows_sent": row["SUM_ROWS_SENT"],
                    "full_join_count": row["SUM_SELECT_FULL_JOIN"],
                    "full_scan_count": row["SUM_SELECT_SCAN"],
                    "sort_merge_passes": row["SUM_SORT_MERGE_PASSES"],
                }
                patterns.append(entry)

                if row["SUM_SELECT_SCAN"] and int(row["SUM_SELECT_SCAN"]) > 0:
                    full_table_scans.append(entry)
                if row["SUM_SELECT_FULL_JOIN"] and int(row["SUM_SELECT_FULL_JOIN"]) > 0:
                    full_joins.append(entry)

            return {
                "top_queries": patterns,
                "full_table_scans": full_table_scans,
                "full_joins": full_joins,
                "summary": {
                    "total_patterns": len(patterns),
                    "full_table_scan_count": len(full_table_scans),
                    "full_join_count": len(full_joins),
                },
            }
        except Error as e:
            if "performance_schema" in str(e).lower():
                return {"error": "performance_schema 不可用，请确认已启用 performance_schema"}
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def analyze_table_statistics(
    instance_name: str = None,
    instance_id: str = None,
    database: str = None,
    config: RunnableConfig = None,
) -> str:
    """分析表级别的IO统计信息。展示各表的读写操作分布和读写比，帮助识别热点表。"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            query = """
                SELECT
                    OBJECT_NAME,
                    COUNT_READ,
                    COUNT_WRITE,
                    COUNT_FETCH,
                    COUNT_INSERT,
                    COUNT_UPDATE,
                    COUNT_DELETE
                FROM performance_schema.table_io_waits_summary_by_table
                WHERE OBJECT_SCHEMA = %s
                ORDER BY (COUNT_READ + COUNT_WRITE) DESC
                LIMIT 30
            """
            rows = execute_readonly_query(conn, query, (database or "mysql",))

            tables = []
            for row in rows:
                count_read = int(row["COUNT_READ"] or 0)
                count_write = int(row["COUNT_WRITE"] or 0)
                total_ops = count_read + count_write
                read_write_ratio = round(count_read / count_write, 2) if count_write > 0 else float("inf") if count_read > 0 else 0
                tables.append(
                    {
                        "table_name": row["OBJECT_NAME"],
                        "count_read": count_read,
                        "count_write": count_write,
                        "count_fetch": int(row["COUNT_FETCH"] or 0),
                        "count_insert": int(row["COUNT_INSERT"] or 0),
                        "count_update": int(row["COUNT_UPDATE"] or 0),
                        "count_delete": int(row["COUNT_DELETE"] or 0),
                        "total_ops": total_ops,
                        "read_write_ratio": read_write_ratio,
                    }
                )

            return {
                "tables": tables,
                "total_count": len(tables),
            }
        except Error as e:
            if "performance_schema" in str(e).lower():
                return {"error": "performance_schema 不可用，请确认已启用 performance_schema"}
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))
