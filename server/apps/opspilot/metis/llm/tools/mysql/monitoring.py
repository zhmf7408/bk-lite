"""MySQL监控工具集"""

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
    format_duration,
    format_size,
    safe_json_dumps,
)


@tool()
def get_database_metrics(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """获取MySQL数据库全局性能指标，包括QPS、TPS、连接数、运行时间、网络流量和慢查询等核心监控数据"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            status_keys = [
                "Questions",
                "Com_select",
                "Com_insert",
                "Com_update",
                "Com_delete",
                "Threads_connected",
                "Threads_running",
                "Uptime",
                "Bytes_received",
                "Bytes_sent",
                "Slow_queries",
            ]
            cursor = conn.cursor()
            try:
                cursor.execute("SHOW GLOBAL STATUS")
                all_status = {row[0]: row[1] for row in cursor.fetchall()}
            finally:
                cursor.close()

            metrics = {}
            for key in status_keys:
                val = all_status.get(key, "0")
                metrics[key] = int(val) if val.isdigit() else val

            uptime = metrics.get("Uptime", 1) or 1
            questions = metrics.get("Questions", 0)
            com_insert = metrics.get("Com_insert", 0)
            com_update = metrics.get("Com_update", 0)
            com_delete = metrics.get("Com_delete", 0)

            metrics["QPS"] = round(questions / uptime, 2)
            metrics["TPS"] = round((com_insert + com_update + com_delete) / uptime, 2)
            metrics["Bytes_received_formatted"] = format_size(metrics.get("Bytes_received", 0))
            metrics["Bytes_sent_formatted"] = format_size(metrics.get("Bytes_sent", 0))
            metrics["Uptime_formatted"] = format_duration(uptime * 1000)

            return metrics
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def get_table_metrics(database: str = None, instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """获取指定数据库中所有表的详细指标，包括行数、数据大小、索引大小、碎片率、自增值和创建/更新时间"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            db = database or item["config"].get("database", "mysql")
            query = """
                SELECT TABLE_NAME, ENGINE, TABLE_ROWS,
                       DATA_LENGTH, INDEX_LENGTH, DATA_FREE,
                       AUTO_INCREMENT, CREATE_TIME, UPDATE_TIME
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY DATA_LENGTH + INDEX_LENGTH DESC
            """
            rows = execute_readonly_query(conn, query, (db,))

            tables = []
            for row in rows:
                data_length = int(row.get("DATA_LENGTH") or 0)
                index_length = int(row.get("INDEX_LENGTH") or 0)
                data_free = int(row.get("DATA_FREE") or 0)
                total_size = data_length + index_length
                frag_ratio = calculate_percentage(data_free, total_size) if total_size > 0 else 0.0

                tables.append(
                    {
                        "table_name": row.get("TABLE_NAME"),
                        "engine": row.get("ENGINE"),
                        "table_rows": row.get("TABLE_ROWS"),
                        "data_length": format_size(data_length),
                        "index_length": format_size(index_length),
                        "total_size": format_size(total_size),
                        "data_free": format_size(data_free),
                        "fragmentation_ratio": f"{frag_ratio}%",
                        "auto_increment": row.get("AUTO_INCREMENT"),
                        "create_time": row.get("CREATE_TIME"),
                        "update_time": row.get("UPDATE_TIME"),
                    }
                )

            return {"database": db, "table_count": len(tables), "tables": tables}
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def get_innodb_stats(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """获取InnoDB存储引擎的详细统计信息，包括缓冲池使用率、命中率、行操作统计和锁等待情况"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            status_keys = [
                "Innodb_buffer_pool_pages_total",
                "Innodb_buffer_pool_pages_data",
                "Innodb_buffer_pool_pages_free",
                "Innodb_buffer_pool_pages_dirty",
                "Innodb_buffer_pool_read_requests",
                "Innodb_buffer_pool_reads",
                "Innodb_rows_read",
                "Innodb_rows_inserted",
                "Innodb_rows_updated",
                "Innodb_rows_deleted",
                "Innodb_row_lock_waits",
                "Innodb_row_lock_time",
            ]
            cursor = conn.cursor()
            try:
                cursor.execute("SHOW GLOBAL STATUS")
                all_status = {row[0]: row[1] for row in cursor.fetchall()}
            finally:
                cursor.close()

            metrics = {}
            for key in status_keys:
                val = all_status.get(key, "0")
                metrics[key] = int(val) if val.isdigit() else val

            read_requests = metrics.get("Innodb_buffer_pool_read_requests", 0)
            reads = metrics.get("Innodb_buffer_pool_reads", 0)
            total_requests = read_requests + reads
            hit_ratio = calculate_percentage(read_requests, total_requests) if total_requests > 0 else 100.0

            pages_total = metrics.get("Innodb_buffer_pool_pages_total", 0)
            pages_data = metrics.get("Innodb_buffer_pool_pages_data", 0)
            pool_usage = calculate_percentage(pages_data, pages_total) if pages_total > 0 else 0.0

            metrics["buffer_pool_hit_ratio"] = f"{hit_ratio}%"
            metrics["buffer_pool_usage"] = f"{pool_usage}%"
            metrics["Innodb_row_lock_time_formatted"] = format_duration(metrics.get("Innodb_row_lock_time", 0))

            return metrics
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def get_io_stats(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """获取MySQL文件IO统计信息，包括各文件的读写次数、字节数和延迟，按总IO量降序排列前20条"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            query = """
                SELECT FILE_NAME,
                       COUNT_READ,
                       COUNT_WRITE,
                       SUM_NUMBER_OF_BYTES_READ,
                       SUM_NUMBER_OF_BYTES_WRITE,
                       SUM_TIMER_READ / 1000000000 AS read_latency_ms,
                       SUM_TIMER_WRITE / 1000000000 AS write_latency_ms
                FROM performance_schema.file_summary_by_instance
                ORDER BY (COUNT_READ + COUNT_WRITE) DESC
                LIMIT 20
            """
            rows = execute_readonly_query(conn, query)

            io_stats = []
            for row in rows:
                io_stats.append(
                    {
                        "file_name": row.get("FILE_NAME"),
                        "count_read": row.get("COUNT_READ"),
                        "count_write": row.get("COUNT_WRITE"),
                        "bytes_read": format_size(row.get("SUM_NUMBER_OF_BYTES_READ", 0)),
                        "bytes_write": format_size(row.get("SUM_NUMBER_OF_BYTES_WRITE", 0)),
                        "read_latency": format_duration(row.get("read_latency_ms", 0)),
                        "write_latency": format_duration(row.get("write_latency_ms", 0)),
                    }
                )

            return {"io_file_count": len(io_stats), "io_stats": io_stats}
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def check_binary_log_status(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """检查MySQL二进制日志状态，包括binlog是否开启、格式、过期策略以及各binlog文件大小和总量"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            cursor = conn.cursor()
            try:
                # Get binlog variables
                cursor.execute("SHOW GLOBAL VARIABLES LIKE 'log_bin'")
                log_bin_row = cursor.fetchone()
                log_bin = log_bin_row[1] if log_bin_row else "OFF"

                cursor.execute("SHOW GLOBAL VARIABLES LIKE 'binlog_format'")
                format_row = cursor.fetchone()
                binlog_format = format_row[1] if format_row else "UNKNOWN"

                cursor.execute("SHOW GLOBAL VARIABLES LIKE 'expire_logs_days'")
                expire_row = cursor.fetchone()
                expire_logs_days = expire_row[1] if expire_row else "0"

                cursor.execute("SHOW GLOBAL VARIABLES LIKE 'binlog_expire_logs_seconds'")
                expire_sec_row = cursor.fetchone()
                binlog_expire_logs_seconds = expire_sec_row[1] if expire_sec_row else "0"

                # Get binary logs list
                binlog_files = []
                total_size = 0
                if log_bin.upper() in ("ON", "1", "YES"):
                    try:
                        cursor.execute("SHOW BINARY LOGS")
                        for row in cursor.fetchall():
                            file_size = int(row[1]) if row[1] else 0
                            binlog_files.append(
                                {
                                    "log_name": row[0],
                                    "file_size": format_size(file_size),
                                    "file_size_bytes": file_size,
                                }
                            )
                            total_size += file_size
                    except Error:
                        binlog_files = []

            finally:
                cursor.close()

            return {
                "log_bin": log_bin,
                "binlog_format": binlog_format,
                "expire_logs_days": expire_logs_days,
                "binlog_expire_logs_seconds": binlog_expire_logs_seconds,
                "binlog_file_count": len(binlog_files),
                "total_binlog_size": format_size(total_size),
                "binlog_files": binlog_files,
            }
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def check_replication_status(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """检查MySQL复制状态，包括主从连接信息、IO/SQL线程状态、复制延迟、GTID集合和错误信息"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            cursor = conn.cursor(dictionary=True)
            try:
                # Try SHOW REPLICA STATUS first (MySQL 8.0.22+), fallback to SHOW SLAVE STATUS
                replica_status = None
                try:
                    cursor.execute("SHOW REPLICA STATUS")
                    replica_status = cursor.fetchone()
                except Error:
                    cursor.execute("SHOW SLAVE STATUS")
                    replica_status = cursor.fetchone()
            finally:
                cursor.close()

            if not replica_status:
                return {"replication_configured": False, "message": "未配置复制"}

            # Normalize field names (REPLICA vs SLAVE naming)
            def _get(key_new, key_old):
                return replica_status.get(key_new) or replica_status.get(key_old)

            return {
                "replication_configured": True,
                "source_host": _get("Source_Host", "Master_Host"),
                "source_port": _get("Source_Port", "Master_Port"),
                "replica_io_running": _get("Replica_IO_Running", "Slave_IO_Running"),
                "replica_sql_running": _get("Replica_SQL_Running", "Slave_SQL_Running"),
                "seconds_behind_source": _get("Seconds_Behind_Source", "Seconds_Behind_Master"),
                "retrieved_gtid_set": _get("Retrieved_Gtid_Set", "Retrieved_Gtid_Set"),
                "executed_gtid_set": _get("Executed_Gtid_Set", "Executed_Gtid_Set"),
                "last_io_error": _get("Last_IO_Error", "Last_IO_Error"),
                "last_sql_error": _get("Last_SQL_Error", "Last_SQL_Error"),
                "relay_log_space": format_size(_get("Relay_Log_Space", "Relay_Log_Space") or 0),
            }
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def get_processlist(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """获取MySQL当前活动进程列表，显示正在执行的查询、连接用户、来源主机、执行时间和状态等信息"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SHOW FULL PROCESSLIST")
                rows = cursor.fetchall()
            finally:
                cursor.close()

            processes = []
            for row in rows:
                command = row.get("Command", "")
                info = row.get("Info")
                # Filter out sleeping connections with no query
                if command == "Sleep" and not info:
                    continue
                processes.append(
                    {
                        "id": row.get("Id"),
                        "user": row.get("User"),
                        "host": row.get("Host"),
                        "db": row.get("db"),
                        "command": command,
                        "time": row.get("Time"),
                        "state": row.get("State"),
                        "info": info,
                    }
                )

            return {"active_process_count": len(processes), "processes": processes}
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def check_database_size_growth(database: str = None, instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """查看数据库磁盘空间使用情况，按库汇总数据量和表数量；如指定数据库则额外展示各表空间明细"""
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            # Summary by schema
            summary_query = """
                SELECT TABLE_SCHEMA,
                       SUM(DATA_LENGTH + INDEX_LENGTH) AS total_size,
                       COUNT(*) AS table_count
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
                GROUP BY TABLE_SCHEMA
                ORDER BY total_size DESC
            """
            summary_rows = execute_readonly_query(conn, summary_query)

            databases = []
            for row in summary_rows:
                databases.append(
                    {
                        "database": row.get("TABLE_SCHEMA"),
                        "total_size": format_size(row.get("total_size", 0)),
                        "total_size_bytes": int(row.get("total_size") or 0),
                        "table_count": row.get("table_count"),
                    }
                )

            result = {"databases": databases}

            # Per-table breakdown if database specified
            if database:
                table_query = """
                    SELECT TABLE_NAME,
                           DATA_LENGTH + INDEX_LENGTH AS total_size,
                           DATA_LENGTH,
                           INDEX_LENGTH,
                           TABLE_ROWS
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY total_size DESC
                """
                table_rows = execute_readonly_query(conn, table_query, (database,))

                tables = []
                for row in table_rows:
                    tables.append(
                        {
                            "table_name": row.get("TABLE_NAME"),
                            "total_size": format_size(row.get("total_size", 0)),
                            "data_length": format_size(row.get("DATA_LENGTH", 0)),
                            "index_length": format_size(row.get("INDEX_LENGTH", 0)),
                            "table_rows": row.get("TABLE_ROWS"),
                        }
                    )

                result["database_detail"] = {"database": database, "tables": tables}

            return result
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))
