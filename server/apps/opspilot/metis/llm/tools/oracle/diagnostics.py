"""Oracle故障诊断工具"""

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
    format_duration,
    format_size,
    safe_json_dumps,
)


@tool()
def diagnose_slow_queries(
    top_n: int = 10,
    instance_name: str = None,
    instance_id: str = None,
    config: RunnableConfig = None,
) -> str:
    """
    诊断Oracle慢查询，返回TOP N耗时最长的SQL

    **何时使用此工具:**
    - 用户反馈"系统慢"、"查询慢"
    - 性能分析和优化
    - 定期巡检慢查询

    **工具能力:**
    - 基于v$sql识别耗时最长的SQL语句
    - 显示SQL执行次数、累计耗时、CPU时间
    - 显示逻辑读(buffer_gets)和物理读(disk_reads)

    Args:
        top_n (int, optional): 返回结果数量，默认10
        instance_name (str, optional): Oracle实例名称
        instance_id (str, optional): Oracle实例ID
        config (RunnableConfig): 工具配置

    Returns:
        JSON格式，包含慢查询列表
    """
    normalized = build_oracle_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_oracle_connection_from_item(item)
        try:
            query = f"""
            SELECT sql_id,
                   SUBSTR(sql_text, 1, 200) AS sql_text,
                   executions,
                   elapsed_time,
                   cpu_time,
                   buffer_gets,
                   disk_reads
            FROM v$sql
            ORDER BY elapsed_time DESC
            FETCH FIRST {int(top_n)} ROWS ONLY
            """
            results = execute_readonly_query(conn, query)
            for row in results:
                row["elapsed_time_formatted"] = format_duration(row.get("ELAPSED_TIME", 0) / 1000 if row.get("ELAPSED_TIME") else 0)
                row["cpu_time_formatted"] = format_duration(row.get("CPU_TIME", 0) / 1000 if row.get("CPU_TIME") else 0)
                executions = row.get("EXECUTIONS", 0) or 1
                row["avg_elapsed_us"] = round(row.get("ELAPSED_TIME", 0) / executions, 2)
            return {"total_slow_queries": len(results), "slow_queries": results}
        except oracledb.Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def diagnose_lock_conflicts(
    instance_name: str = None,
    instance_id: str = None,
    config: RunnableConfig = None,
) -> str:
    """
    诊断Oracle锁冲突和等待

    **何时使用此工具:**
    - 用户反馈"查询卡住"、"事务阻塞"
    - 排查锁等待问题
    - 分析锁冲突情况

    **工具能力:**
    - 检测当前锁等待和阻塞关系
    - 显示阻塞方和等待方的会话信息
    - 尝试查询dba_waiters获取更多详情
    - 兼容无DBA权限的场景

    Args:
        instance_name (str, optional): Oracle实例名称
        instance_id (str, optional): Oracle实例ID
        config (RunnableConfig): 工具配置

    Returns:
        JSON格式，包含锁冲突列表
    """
    normalized = build_oracle_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_oracle_connection_from_item(item)
        try:
            # 通过v$lock和v$session查找阻塞关系
            lock_query = """
            SELECT
                blocker.sid AS blocker_sid,
                blocker.serial# AS blocker_serial,
                blocker.username AS blocker_username,
                blocker.program AS blocker_program,
                blocker.status AS blocker_status,
                blocker.sql_id AS blocker_sql_id,
                waiter.sid AS waiter_sid,
                waiter.serial# AS waiter_serial,
                waiter.username AS waiter_username,
                waiter.program AS waiter_program,
                waiter.sql_id AS waiter_sql_id,
                waiter.seconds_in_wait AS wait_seconds,
                waiter.event AS wait_event,
                w.type AS lock_type,
                w.lmode AS lock_lmode,
                w.request AS lock_request
            FROM v$lock w
            JOIN v$lock b
                ON w.id1 = b.id1
                AND w.id2 = b.id2
                AND w.request > 0
                AND b.lmode > 0
                AND w.sid != b.sid
            JOIN v$session waiter ON w.sid = waiter.sid
            JOIN v$session blocker ON b.sid = blocker.sid
            """
            results = execute_readonly_query(conn, lock_query)

            # 尝试查询dba_waiters获取额外信息
            dba_waiters = []
            try:
                dba_query = """
                SELECT waiting_session, holding_session, lock_type, mode_held, mode_requested
                FROM dba_waiters
                """
                dba_waiters = execute_readonly_query(conn, dba_query)
            except oracledb.Error:
                pass  # 无DBA权限时忽略

            return {
                "total_lock_conflicts": len(results),
                "lock_conflicts": results,
                "has_conflicts": len(results) > 0,
                "dba_waiters": dba_waiters,
            }
        except oracledb.Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def diagnose_connection_issues(
    instance_name: str = None,
    instance_id: str = None,
    config: RunnableConfig = None,
) -> str:
    """
    诊断Oracle连接问题

    **何时使用此工具:**
    - 用户反馈"无法连接数据库"
    - 检查连接数是否达到上限
    - 分析连接使用情况

    **工具能力:**
    - 对比当前会话数与processes/sessions参数限制
    - 显示活跃/非活跃会话分布
    - 按用户统计连接数
    - 提供连接相关告警

    Args:
        instance_name (str, optional): Oracle实例名称
        instance_id (str, optional): Oracle实例ID
        config (RunnableConfig): 工具配置

    Returns:
        JSON格式，包含连接统计信息
    """
    normalized = build_oracle_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_oracle_connection_from_item(item)
        try:
            # 获取processes和sessions参数限制
            param_query = """
            SELECT name, value
            FROM v$parameter
            WHERE name IN ('processes', 'sessions')
            """
            param_rows = execute_readonly_query(conn, param_query)
            params = {row["NAME"]: int(row["VALUE"]) for row in param_rows}
            max_processes = params.get("processes", 150)
            max_sessions = params.get("sessions", 170)

            # 当前会话总数及活跃/非活跃分布
            session_query = """
            SELECT status, COUNT(*) AS cnt
            FROM v$session
            GROUP BY status
            """
            session_rows = execute_readonly_query(conn, session_query)
            status_breakdown = {row["STATUS"]: row["CNT"] for row in session_rows}
            total_sessions = sum(status_breakdown.values())
            active_sessions = status_breakdown.get("ACTIVE", 0)
            inactive_sessions = status_breakdown.get("INACTIVE", 0)

            # 按用户统计连接数
            user_query = """
            SELECT username, COUNT(*) AS cnt
            FROM v$session
            WHERE username IS NOT NULL
            GROUP BY username
            ORDER BY cnt DESC
            """
            user_rows = execute_readonly_query(conn, user_query)

            session_usage = calculate_percentage(total_sessions, max_sessions)

            warnings = []
            if session_usage > 90:
                warnings.append("会话数使用率超过90%，建议立即检查并释放空闲连接或增大sessions参数")
            elif session_usage > 80:
                warnings.append("会话数使用率超过80%，建议关注连接增长趋势")

            return {
                "max_processes": max_processes,
                "max_sessions": max_sessions,
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "inactive_sessions": inactive_sessions,
                "status_breakdown": status_breakdown,
                "session_usage_percent": session_usage,
                "is_near_limit": session_usage > 80,
                "per_user_connections": user_rows,
                "warnings": warnings,
            }
        except oracledb.Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def check_database_health(
    instance_name: str = None,
    instance_id: str = None,
    config: RunnableConfig = None,
) -> str:
    """
    Oracle数据库综合健康检查

    **何时使用此工具:**
    - 定期健康巡检
    - 快速了解数据库整体状态
    - 发现潜在问题

    **工具能力:**
    - 检查实例状态（v$instance）
    - 检查表空间使用率（>85%告警）
    - 检查活跃会话数与限制的比值
    - 检查缓冲区缓存命中率
    - 检查无效对象数量
    - 综合评估健康状态

    Args:
        instance_name (str, optional): Oracle实例名称
        instance_id (str, optional): Oracle实例ID
        config (RunnableConfig): 工具配置

    Returns:
        JSON格式，包含健康检查结果
    """
    normalized = build_oracle_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_oracle_connection_from_item(item)
        try:
            checks = {}
            health_score = 100
            issues = []

            # 1. 实例状态
            try:
                inst_query = """
                SELECT instance_name, host_name, version, status, database_status, startup_time
                FROM v$instance
                """
                inst_rows = execute_readonly_query(conn, inst_query)
                if inst_rows:
                    inst = inst_rows[0]
                    inst_status = inst.get("STATUS", "UNKNOWN")
                    db_status = inst.get("DATABASE_STATUS", "UNKNOWN")
                    checks["instance"] = {
                        "status": "ok" if inst_status == "OPEN" else "critical",
                        "instance_name": inst.get("INSTANCE_NAME"),
                        "host_name": inst.get("HOST_NAME"),
                        "version": inst.get("VERSION"),
                        "instance_status": inst_status,
                        "database_status": db_status,
                        "startup_time": inst.get("STARTUP_TIME"),
                    }
                    if inst_status != "OPEN":
                        issues.append(f"实例状态异常: {inst_status}")
                        health_score -= 30
            except oracledb.Error as e:
                checks["instance"] = {"status": "error", "error": str(e)}

            # 2. 表空间使用率
            try:
                ts_query = """
                SELECT
                    df.tablespace_name,
                    df.total_bytes,
                    NVL(fs.free_bytes, 0) AS free_bytes,
                    df.total_bytes - NVL(fs.free_bytes, 0) AS used_bytes,
                    ROUND((df.total_bytes - NVL(fs.free_bytes, 0)) / df.total_bytes * 100, 2) AS usage_pct
                FROM
                    (SELECT tablespace_name, SUM(bytes) AS total_bytes FROM dba_data_files GROUP BY tablespace_name) df
                LEFT JOIN
                    (SELECT tablespace_name, SUM(bytes) AS free_bytes FROM dba_free_space GROUP BY tablespace_name) fs
                ON df.tablespace_name = fs.tablespace_name
                ORDER BY usage_pct DESC
                """
                ts_rows = execute_readonly_query(conn, ts_query)
                ts_warnings = []
                for ts in ts_rows:
                    pct = ts.get("USAGE_PCT", 0)
                    name = ts.get("TABLESPACE_NAME", "")
                    ts["total_formatted"] = format_size(ts.get("TOTAL_BYTES", 0))
                    ts["used_formatted"] = format_size(ts.get("USED_BYTES", 0))
                    ts["free_formatted"] = format_size(ts.get("FREE_BYTES", 0))
                    if pct and pct > 85:
                        ts_warnings.append(f"表空间 {name} 使用率 {pct}%")
                checks["tablespace"] = {
                    "status": "warning" if ts_warnings else "ok",
                    "tablespaces": ts_rows,
                    "warnings": ts_warnings,
                }
                if ts_warnings:
                    issues.extend(ts_warnings)
                    health_score -= 5 * len(ts_warnings)
            except oracledb.Error as e:
                checks["tablespace"] = {"status": "error", "error": str(e)}

            # 3. 活跃会话 vs 限制
            try:
                sess_query = """
                SELECT COUNT(*) AS total_sessions,
                       SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) AS active_sessions
                FROM v$session
                """
                sess_rows = execute_readonly_query(conn, sess_query)
                total_sess = sess_rows[0]["TOTAL_SESSIONS"] if sess_rows else 0

                limit_query = "SELECT value FROM v$parameter WHERE name = 'sessions'"
                limit_rows = execute_readonly_query(conn, limit_query)
                max_sess = int(limit_rows[0]["VALUE"]) if limit_rows else 170

                sess_usage = calculate_percentage(total_sess, max_sess)
                checks["sessions"] = {
                    "status": "critical" if sess_usage > 90 else ("warning" if sess_usage > 80 else "ok"),
                    "total_sessions": total_sess,
                    "active_sessions": sess_rows[0].get("ACTIVE_SESSIONS", 0) if sess_rows else 0,
                    "max_sessions": max_sess,
                    "usage_percent": sess_usage,
                }
                if sess_usage > 90:
                    issues.append(f"会话数使用率 {sess_usage}%，已接近上限")
                    health_score -= 20
                elif sess_usage > 80:
                    issues.append(f"会话数使用率 {sess_usage}%")
                    health_score -= 10
            except oracledb.Error as e:
                checks["sessions"] = {"status": "error", "error": str(e)}

            # 4. 缓冲区缓存命中率
            try:
                cache_query = """
                SELECT
                    SUM(CASE WHEN name = 'consistent gets' THEN value ELSE 0 END) +
                    SUM(CASE WHEN name = 'db block gets' THEN value ELSE 0 END) AS logical_reads,
                    SUM(CASE WHEN name = 'physical reads' THEN value ELSE 0 END) AS physical_reads
                FROM v$sysstat
                WHERE name IN ('consistent gets', 'db block gets', 'physical reads')
                """
                cache_rows = execute_readonly_query(conn, cache_query)
                if cache_rows:
                    logical = cache_rows[0].get("LOGICAL_READS", 0) or 0
                    physical = cache_rows[0].get("PHYSICAL_READS", 0) or 0
                    hit_ratio = calculate_percentage(logical - physical, logical) if logical > 0 else 100.0
                    checks["buffer_cache"] = {
                        "status": "ok" if hit_ratio >= 95 else ("warning" if hit_ratio >= 85 else "critical"),
                        "hit_ratio": hit_ratio,
                        "logical_reads": logical,
                        "physical_reads": physical,
                    }
                    if hit_ratio < 95:
                        issues.append(f"缓冲区缓存命中率偏低: {hit_ratio}%")
                        health_score -= 15
            except oracledb.Error as e:
                checks["buffer_cache"] = {"status": "error", "error": str(e)}

            # 5. 无效对象数量
            try:
                invalid_query = """
                SELECT COUNT(*) AS invalid_count
                FROM dba_objects
                WHERE status = 'INVALID'
                """
                inv_rows = execute_readonly_query(conn, invalid_query)
                invalid_count = inv_rows[0]["INVALID_COUNT"] if inv_rows else 0
                checks["invalid_objects"] = {
                    "status": "warning" if invalid_count > 0 else "ok",
                    "count": invalid_count,
                }
                if invalid_count > 0:
                    issues.append(f"存在 {invalid_count} 个无效对象")
                    health_score -= 5
            except oracledb.Error as e:
                checks["invalid_objects"] = {"status": "error", "error": str(e)}

            health_score = max(health_score, 0)
            if health_score >= 90:
                health_status = "healthy"
            elif health_score >= 70:
                health_status = "warning"
            else:
                health_status = "critical"

            return {
                "health_status": health_status,
                "health_score": health_score,
                "checks": checks,
                "issues": issues,
            }
        except oracledb.Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def check_dataguard_status(
    instance_name: str = None,
    instance_id: str = None,
    config: RunnableConfig = None,
) -> str:
    """
    检查Oracle Data Guard状态和延迟

    **何时使用此工具:**
    - 监控主备库同步状态
    - 排查Data Guard延迟问题
    - 检查备库是否正常接收和应用日志

    **工具能力:**
    - 检查数据库角色（PRIMARY/STANDBY）和保护模式
    - 备库场景：查询传输延迟和应用延迟
    - 主库场景：查询归档目的地状态
    - 优雅处理未配置Data Guard的情况

    Args:
        instance_name (str, optional): Oracle实例名称
        instance_id (str, optional): Oracle实例ID
        config (RunnableConfig): 工具配置

    Returns:
        JSON格式，包含Data Guard状态信息
    """
    normalized = build_oracle_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_oracle_connection_from_item(item)
        try:
            # 获取数据库角色和保护模式
            role_query = """
            SELECT database_role, protection_mode, protection_level, switchover_status, dataguard_broker
            FROM v$database
            """
            role_rows = execute_readonly_query(conn, role_query)
            if not role_rows:
                return {"error": "无法查询v$database"}

            db_info = role_rows[0]
            database_role = db_info.get("DATABASE_ROLE", "UNKNOWN")
            protection_mode = db_info.get("PROTECTION_MODE", "UNKNOWN")
            switchover_status = db_info.get("SWITCHOVER_STATUS", "UNKNOWN")
            broker = db_info.get("DATAGUARD_BROKER", "UNKNOWN")

            result = {
                "database_role": database_role,
                "protection_mode": protection_mode,
                "switchover_status": switchover_status,
                "dataguard_broker": broker,
            }

            if "STANDBY" in database_role.upper():
                # 备库：查询传输延迟和应用延迟
                try:
                    dg_query = """
                    SELECT name, value, time_computed, datum_time
                    FROM v$dataguard_stats
                    WHERE name IN ('transport lag', 'apply lag', 'apply finish time')
                    """
                    dg_rows = execute_readonly_query(conn, dg_query)
                    dg_stats = {row["NAME"]: row.get("VALUE") for row in dg_rows}
                    result["transport_lag"] = dg_stats.get("transport lag")
                    result["apply_lag"] = dg_stats.get("apply lag")
                    result["apply_finish_time"] = dg_stats.get("apply finish time")
                    result["dataguard_stats"] = dg_rows

                    # 判断健康状态
                    has_lag = result["transport_lag"] or result["apply_lag"]
                    result["is_healthy"] = has_lag is not None
                    result["dg_configured"] = True
                except oracledb.Error as e:
                    result["dataguard_stats_error"] = str(e)
                    result["dg_configured"] = False

            elif database_role.upper() == "PRIMARY":
                # 主库：查询归档目的地状态
                try:
                    dest_query = """
                    SELECT dest_id, dest_name, status, type, error,
                           archived_seq#, applied_seq#, gap_status
                    FROM v$archive_dest_status
                    WHERE status != 'INACTIVE' AND type != 'LOCAL'
                    """
                    dest_rows = execute_readonly_query(conn, dest_query)
                    if dest_rows:
                        result["archive_destinations"] = dest_rows
                        result["dg_configured"] = True
                        # 检查是否有错误的目的地
                        error_dests = [d for d in dest_rows if d.get("STATUS") == "ERROR"]
                        result["has_dest_errors"] = len(error_dests) > 0
                        result["error_destinations"] = error_dests
                    else:
                        result["archive_destinations"] = []
                        result["dg_configured"] = False
                        result["message"] = "未发现远程归档目的地，可能未配置Data Guard"
                except oracledb.Error as e:
                    result["archive_dest_error"] = str(e)
                    result["dg_configured"] = False
                    result["message"] = "无法查询归档目的地状态，可能未配置Data Guard"
            else:
                result["dg_configured"] = False
                result["message"] = f"数据库角色为 {database_role}，非标准的PRIMARY/STANDBY角色"

            return result
        except oracledb.Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))
