"""MySQL故障诊断工具"""

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
    safe_json_dumps,
)


@tool()
def diagnose_slow_queries(instance_name: str = None, instance_id: str = None, limit: int = 20, config: RunnableConfig = None) -> str:
    """
    诊断慢查询

    **何时使用此工具:**
    - 用户反馈"系统慢"、"查询慢"
    - 性能分析和优化
    - 定期巡检慢查询

    **工具能力:**
    - 基于performance_schema.events_statements_summary_by_digest识别慢查询
    - 显示查询的平均/总执行时间
    - 显示调用次数、扫描行数、返回行数

    Args:
        instance_name (str, optional): MySQL实例名称
        instance_id (str, optional): MySQL实例ID
        limit (int, optional): 返回结果数量,默认20
        config (RunnableConfig): 工具配置

    Returns:
        JSON格式,包含慢查询列表
    """
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            query = f"""
            SELECT SCHEMA_NAME, DIGEST_TEXT, COUNT_STAR,
                   SUM_TIMER_WAIT/1000000000 as total_time_ms,
                   AVG_TIMER_WAIT/1000000000 as avg_time_ms,
                   SUM_ROWS_EXAMINED, SUM_ROWS_SENT
            FROM performance_schema.events_statements_summary_by_digest
            ORDER BY SUM_TIMER_WAIT DESC
            LIMIT {int(limit)}
            """
            results = execute_readonly_query(conn, query)
            for row in results:
                row["total_time_formatted"] = format_duration(row.get("total_time_ms"))
                row["avg_time_formatted"] = format_duration(row.get("avg_time_ms"))
            return {"total_slow_queries": len(results), "slow_queries": results}
        except Error as e:
            error_msg = str(e)
            if "performance_schema" in error_msg.lower() or "1046" in error_msg or "1142" in error_msg:
                return {"error": "performance_schema不可用，请确认已启用performance_schema（在my.cnf中设置performance_schema=ON并重启MySQL）"}
            return {"error": error_msg}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def diagnose_lock_conflicts(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """
    检测锁冲突和阻塞

    **何时使用此工具:**
    - 用户反馈"查询卡住"、"事务阻塞"
    - 排查锁等待问题
    - 分析锁冲突情况

    **工具能力:**
    - 检测当前锁等待情况
    - 显示阻塞/被阻塞线程信息
    - 显示锁类型、锁模式、涉及的表
    - 兼容MySQL 8.0和更早版本

    Args:
        instance_name (str, optional): MySQL实例名称
        instance_id (str, optional): MySQL实例ID
        config (RunnableConfig): 工具配置

    Returns:
        JSON格式,包含锁冲突列表
    """
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            # MySQL 8.0+ 使用 performance_schema.data_lock_waits
            query_80 = """
            SELECT
                dlw.REQUESTING_THREAD_ID as waiting_thread_id,
                dlw.BLOCKING_THREAD_ID as blocking_thread_id,
                dl_waiting.LOCK_TYPE as waiting_lock_type,
                dl_waiting.LOCK_MODE as waiting_lock_mode,
                dl_waiting.OBJECT_SCHEMA as schema_name,
                dl_waiting.OBJECT_NAME as table_name,
                dl_blocking.LOCK_TYPE as blocking_lock_type,
                dl_blocking.LOCK_MODE as blocking_lock_mode,
                t_waiting.PROCESSLIST_ID as waiting_processlist_id,
                t_blocking.PROCESSLIST_ID as blocking_processlist_id,
                t_waiting.PROCESSLIST_INFO as waiting_query,
                t_blocking.PROCESSLIST_INFO as blocking_query
            FROM performance_schema.data_lock_waits dlw
            JOIN performance_schema.data_locks dl_waiting
                ON dlw.REQUESTING_ENGINE_LOCK_ID = dl_waiting.ENGINE_LOCK_ID
            JOIN performance_schema.data_locks dl_blocking
                ON dlw.BLOCKING_ENGINE_LOCK_ID = dl_blocking.ENGINE_LOCK_ID
            LEFT JOIN performance_schema.threads t_waiting
                ON dlw.REQUESTING_THREAD_ID = t_waiting.THREAD_ID
            LEFT JOIN performance_schema.threads t_blocking
                ON dlw.BLOCKING_THREAD_ID = t_blocking.THREAD_ID
            """
            try:
                results = execute_readonly_query(conn, query_80)
                return {"total_lock_conflicts": len(results), "lock_conflicts": results, "has_conflicts": len(results) > 0}
            except Error:
                pass

            # Fallback: MySQL < 8.0 使用 information_schema
            query_legacy = """
            SELECT
                r.trx_id as waiting_trx_id,
                r.trx_mysql_thread_id as waiting_thread_id,
                r.trx_query as waiting_query,
                b.trx_id as blocking_trx_id,
                b.trx_mysql_thread_id as blocking_thread_id,
                b.trx_query as blocking_query,
                l.lock_table as locked_table,
                l.lock_type as lock_type,
                l.lock_mode as lock_mode,
                w.requesting_lock_id,
                w.blocking_lock_id
            FROM information_schema.INNODB_LOCK_WAITS w
            JOIN information_schema.INNODB_TRX r ON w.requesting_trx_id = r.trx_id
            JOIN information_schema.INNODB_TRX b ON w.blocking_trx_id = b.trx_id
            JOIN information_schema.INNODB_LOCKS l ON w.requesting_lock_id = l.lock_id
            """
            results = execute_readonly_query(conn, query_legacy)
            return {"total_lock_conflicts": len(results), "lock_conflicts": results, "has_conflicts": len(results) > 0}
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def diagnose_connection_issues(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """
    诊断连接池问题

    **何时使用此工具:**
    - 用户反馈"无法连接数据库"
    - 检查连接数是否达到上限
    - 分析连接使用情况

    **工具能力:**
    - 显示当前连接数和最大连接数
    - 显示活跃连接、等待连接、被拒连接数
    - 计算连接池使用率
    - 提供连接相关告警

    Args:
        instance_name (str, optional): MySQL实例名称
        instance_id (str, optional): MySQL实例ID
        config (RunnableConfig): 工具配置

    Returns:
        JSON格式,包含连接统计信息
    """
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            # 获取状态变量
            status_query = """
            SHOW GLOBAL STATUS WHERE Variable_name IN (
                'Threads_connected', 'Threads_running', 'Aborted_connects',
                'Aborted_clients', 'Max_used_connections'
            )
            """
            status_rows = execute_readonly_query(conn, status_query)
            status = {row["Variable_name"]: int(row["Value"]) for row in status_rows}

            # 获取配置变量
            var_query = """
            SHOW GLOBAL VARIABLES WHERE Variable_name IN ('max_connections', 'wait_timeout')
            """
            var_rows = execute_readonly_query(conn, var_query)
            variables = {row["Variable_name"]: int(row["Value"]) for row in var_rows}

            max_connections = variables.get("max_connections", 151)
            threads_connected = status.get("Threads_connected", 0)
            usage_percent = calculate_percentage(threads_connected, max_connections)

            warnings = []
            if usage_percent > 90:
                warnings.append("连接数使用率超过90%，建议立即扩容或优化连接管理")
            elif usage_percent > 80:
                warnings.append("连接数使用率超过80%，建议关注并准备扩容")

            if status.get("Aborted_connects", 0) > 100:
                warnings.append(f"异常断开连接数较多({status['Aborted_connects']})，请检查网络或认证配置")

            return {
                "max_connections": max_connections,
                "threads_connected": threads_connected,
                "threads_running": status.get("Threads_running", 0),
                "aborted_connects": status.get("Aborted_connects", 0),
                "aborted_clients": status.get("Aborted_clients", 0),
                "max_used_connections": status.get("Max_used_connections", 0),
                "wait_timeout": variables.get("wait_timeout", 0),
                "usage_percent": usage_percent,
                "is_near_limit": usage_percent > 80,
                "warnings": warnings,
            }
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def check_database_health(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """
    整体数据库健康检查

    **何时使用此工具:**
    - 定期健康巡检
    - 快速了解数据库状态
    - 发现潜在问题

    **工具能力:**
    - 检查运行时间、连接数、QPS
    - 检查InnoDB缓冲池命中率
    - 检查慢查询数量
    - 综合评估健康状态

    Args:
        instance_name (str, optional): MySQL实例名称
        instance_id (str, optional): MySQL实例ID
        config (RunnableConfig): 工具配置

    Returns:
        JSON格式,包含健康检查结果
    """
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            status_query = """
            SHOW GLOBAL STATUS WHERE Variable_name IN (
                'Uptime', 'Threads_connected', 'Threads_running', 'Questions',
                'Innodb_buffer_pool_read_requests', 'Innodb_buffer_pool_reads',
                'Slow_queries', 'Max_used_connections'
            )
            """
            status_rows = execute_readonly_query(conn, status_query)
            status = {row["Variable_name"]: int(row["Value"]) for row in status_rows}

            var_query = "SHOW GLOBAL VARIABLES WHERE Variable_name = 'max_connections'"
            var_rows = execute_readonly_query(conn, var_query)
            max_connections = int(var_rows[0]["Value"]) if var_rows else 151

            uptime = status.get("Uptime", 0)
            questions = status.get("Questions", 0)
            qps = round(questions / uptime, 2) if uptime > 0 else 0

            bp_read_requests = status.get("Innodb_buffer_pool_read_requests", 0)
            bp_reads = status.get("Innodb_buffer_pool_reads", 0)
            bp_hit_ratio = calculate_percentage(bp_read_requests - bp_reads, bp_read_requests) if bp_read_requests > 0 else 100.0

            threads_connected = status.get("Threads_connected", 0)
            conn_usage = calculate_percentage(threads_connected, max_connections)

            issues = []
            health_score = 100

            if conn_usage > 90:
                issues.append("连接数超过90%")
                health_score -= 20
            elif conn_usage > 80:
                issues.append("连接数超过80%")
                health_score -= 10

            if bp_hit_ratio < 95:
                issues.append(f"InnoDB缓冲池命中率偏低({bp_hit_ratio}%)")
                health_score -= 15

            if status.get("Slow_queries", 0) > 100:
                issues.append(f"慢查询数量较多({status['Slow_queries']})")
                health_score -= 10

            if health_score >= 90:
                health_status = "healthy"
            elif health_score >= 70:
                health_status = "warning"
            else:
                health_status = "critical"

            return {
                "health_status": health_status,
                "health_score": health_score,
                "uptime_seconds": uptime,
                "uptime_formatted": format_duration(uptime * 1000),
                "threads_connected": threads_connected,
                "threads_running": status.get("Threads_running", 0),
                "qps": qps,
                "buffer_pool_hit_ratio": bp_hit_ratio,
                "slow_queries": status.get("Slow_queries", 0),
                "max_connections": max_connections,
                "connection_usage_percent": conn_usage,
                "issues": issues,
            }
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def check_replication_lag(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """
    检查MySQL复制延迟

    **何时使用此工具:**
    - 监控主从复制延迟
    - 排查数据不一致问题
    - 检查从库健康状态

    **工具能力:**
    - 兼容MySQL 8.0.22+（SHOW REPLICA STATUS）和旧版（SHOW SLAVE STATUS）
    - 显示复制延迟秒数
    - 显示IO线程和SQL线程状态
    - 显示最近的复制错误

    Args:
        instance_name (str, optional): MySQL实例名称
        instance_id (str, optional): MySQL实例ID
        config (RunnableConfig): 工具配置

    Returns:
        JSON格式,包含复制状态信息
    """
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            # 尝试 MySQL 8.0.22+ 语法
            try:
                cursor = conn.cursor()
                cursor.execute("SHOW REPLICA STATUS")
                columns = [col[0] for col in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                cursor.close()
            except Error:
                cursor = conn.cursor()
                cursor.execute("SHOW SLAVE STATUS")
                columns = [col[0] for col in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                cursor.close()

            if not rows:
                return {"has_replication": False, "message": "当前实例未配置复制"}

            row = dict(zip(columns, rows[0]))

            # 兼容新旧字段名
            seconds_behind = row.get("Seconds_Behind_Source", row.get("Seconds_Behind_Master"))
            io_running = row.get("Replica_IO_Running", row.get("Slave_IO_Running"))
            sql_running = row.get("Replica_SQL_Running", row.get("Slave_SQL_Running"))
            last_error = row.get("Last_Error", "")

            return {
                "has_replication": True,
                "seconds_behind": seconds_behind,
                "io_running": io_running,
                "sql_running": sql_running,
                "last_error": last_error if last_error else None,
                "is_healthy": io_running == "Yes" and sql_running == "Yes" and (seconds_behind is not None and seconds_behind < 60),
            }
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def diagnose_deadlocks(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """
    诊断死锁问题

    **何时使用此工具:**
    - 应用报告死锁错误
    - 排查事务冲突
    - 分析最近的死锁情况

    **工具能力:**
    - 从SHOW ENGINE INNODB STATUS中提取死锁信息
    - 解析最近一次死锁的详细内容
    - 帮助识别死锁模式

    Args:
        instance_name (str, optional): MySQL实例名称
        instance_id (str, optional): MySQL实例ID
        config (RunnableConfig): 工具配置

    Returns:
        JSON格式,包含死锁诊断信息
    """
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            cursor = conn.cursor()
            cursor.execute("SHOW ENGINE INNODB STATUS")
            row = cursor.fetchone()
            cursor.close()

            if not row:
                return {"deadlock_detected": False, "message": "无法获取InnoDB状态信息"}

            innodb_status = row[2] if len(row) > 2 else str(row)

            # 解析 LATEST DETECTED DEADLOCK 段落
            deadlock_section = ""
            in_deadlock = False
            for line in innodb_status.split("\n"):
                if "LATEST DETECTED DEADLOCK" in line:
                    in_deadlock = True
                    deadlock_section = line + "\n"
                    continue
                if in_deadlock:
                    if line.startswith("---") and "---" in line and deadlock_section.count("---") >= 2:
                        # 遇到下一个段落分隔符，结束
                        break
                    deadlock_section += line + "\n"

            if deadlock_section.strip():
                return {
                    "deadlock_detected": True,
                    "deadlock_info": deadlock_section.strip()[:4000],
                    "recommendations": ["分析死锁图确定冲突的资源", "考虑调整事务隔离级别", "优化访问顺序以避免循环等待"],
                }
            else:
                return {"deadlock_detected": False, "message": "No deadlock detected"}
        except Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def get_failed_queries(instance_name: str = None, instance_id: str = None, config: RunnableConfig = None) -> str:
    """
    获取失败和错误的查询信息

    **何时使用此工具:**
    - 排查应用错误
    - 分析查询失败原因
    - 监控数据库错误率

    **工具能力:**
    - 从performance_schema获取产生错误的查询摘要
    - 显示错误次数、警告次数
    - 按错误次数降序排列

    Args:
        instance_name (str, optional): MySQL实例名称
        instance_id (str, optional): MySQL实例ID
        config (RunnableConfig): 工具配置

    Returns:
        JSON格式,包含失败查询统计
    """
    normalized = build_mysql_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_mysql_connection_from_item(item)
        try:
            query = """
            SELECT SCHEMA_NAME, DIGEST_TEXT, COUNT_STAR, SUM_ERRORS, SUM_WARNINGS
            FROM performance_schema.events_statements_summary_by_digest
            WHERE SUM_ERRORS > 0
            ORDER BY SUM_ERRORS DESC
            LIMIT 20
            """
            results = execute_readonly_query(conn, query)
            return {"total_failed_queries": len(results), "failed_queries": results}
        except Error as e:
            error_msg = str(e)
            if "performance_schema" in error_msg.lower() or "1046" in error_msg or "1142" in error_msg:
                return {"error": "performance_schema不可用，请确认已启用performance_schema（在my.cnf中设置performance_schema=ON并重启MySQL）"}
            return {"error": error_msg}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))
