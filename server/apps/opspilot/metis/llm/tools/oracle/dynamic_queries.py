"""Oracle动态SQL查询工具 - 安全的动态查询生成和执行"""

import re

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

import oracledb

from apps.opspilot.metis.llm.tools.common.credentials import execute_with_credentials
from apps.opspilot.metis.llm.tools.oracle.connection import (
    build_oracle_normalized_from_runnable,
    get_oracle_connection_from_item,
)
from apps.opspilot.metis.llm.tools.oracle.utils import (
    execute_readonly_query,
    safe_json_dumps,
    validate_sql_safety,
)

SENSITIVE_COLUMNS = {
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
    "credential",
    "auth",
}


@tool()
def search_tables_by_keyword(
    keyword: str,
    db_schema: str = None,
    instance_name: str = None,
    instance_id: str = None,
    config: RunnableConfig = None,
) -> str:
    """按关键字搜索Oracle表名和列名，在ALL_TABLES和ALL_TAB_COLUMNS中匹配"""
    normalized = build_oracle_normalized_from_runnable(config, instance_name, instance_id)

    def _executor(item):
        conn = get_oracle_connection_from_item(item)
        try:
            pattern = f"%{keyword.upper()}%"

            if db_schema:
                owner_filter = "AND OWNER = :owner"
                tables_params = {"pattern": pattern, "owner": db_schema.upper()}
                columns_params = {"pattern": pattern, "owner": db_schema.upper()}
            else:
                owner_filter = ""
                tables_params = {"pattern": pattern}
                columns_params = {"pattern": pattern}

            # 搜索表名
            tables_query = f"""
                SELECT OWNER, TABLE_NAME, NUM_ROWS
                FROM ALL_TABLES
                WHERE TABLE_NAME LIKE :pattern
                  {owner_filter}
                ORDER BY NUM_ROWS DESC NULLS LAST
                FETCH FIRST 50 ROWS ONLY
            """
            tables = execute_readonly_query(conn, tables_query, tables_params)

            # 搜索列名
            columns_query = f"""
                SELECT OWNER, TABLE_NAME, COLUMN_NAME, DATA_TYPE
                FROM ALL_TAB_COLUMNS
                WHERE COLUMN_NAME LIKE :pattern
                  {owner_filter}
                ORDER BY OWNER, TABLE_NAME, COLUMN_ID
                FETCH FIRST 50 ROWS ONLY
            """
            columns = execute_readonly_query(conn, columns_query, columns_params)

            return {
                "keyword": keyword,
                "schema": db_schema,
                "matching_tables": tables,
                "matching_columns": columns,
            }
        except oracledb.Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def execute_safe_select(
    sql: str,
    instance_name: str = None,
    instance_id: str = None,
    config: RunnableConfig = None,
) -> str:
    """安全执行Oracle SELECT查询（只读模式），禁止写操作和SELECT *，自动过滤敏感列并限制返回行数"""
    normalized = build_oracle_normalized_from_runnable(config, instance_name, instance_id)

    # 安全验证
    is_safe, error_msg = validate_sql_safety(sql)
    if not is_safe:
        return safe_json_dumps({"error": f"SQL安全检查失败: {error_msg}", "sql": sql})

    # 禁止 SELECT *
    sql_normalized = " ".join(sql.lower().split())
    if re.search(r"\bselect\s+\*\s+from\b", sql_normalized):
        return safe_json_dumps(
            {
                "error": "安全限制: 禁止使用SELECT *，必须明确指定需要查询的列名",
                "sql": sql,
                "suggestion": "请先查看表结构，然后明确指定需要的列",
            }
        )

    def _executor(item):
        conn = get_oracle_connection_from_item(item)
        try:
            # 添加行数限制
            query = sql.rstrip().rstrip(";")
            if "fetch" not in query.lower() and "rownum" not in query.lower():
                query = f"SELECT * FROM ({query}) WHERE ROWNUM <= 100"

            # 使用只读事务执行
            cursor = conn.cursor()
            try:
                cursor.execute("SET TRANSACTION READ ONLY")
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchmany(100)
                results = [dict(zip(columns, row)) for row in rows]
            finally:
                cursor.close()

            # 过滤敏感列
            if results:
                keys_to_remove = [k for k in results[0] if k.lower() in SENSITIVE_COLUMNS]
                if keys_to_remove:
                    results = [{k: v for k, v in row.items() if k not in keys_to_remove} for row in results]

            return {
                "success": True,
                "row_count": len(results),
                "sql": query,
                "data": results[:100],
            }
        except oracledb.Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))


@tool()
def explain_query_plan(
    sql: str,
    instance_name: str = None,
    instance_id: str = None,
    config: RunnableConfig = None,
) -> str:
    """获取Oracle SQL执行计划，用于分析和优化SQL性能"""
    normalized = build_oracle_normalized_from_runnable(config, instance_name, instance_id)

    is_safe, error_msg = validate_sql_safety(sql)
    if not is_safe:
        return safe_json_dumps({"error": f"SQL安全检查失败: {error_msg}", "sql": sql})

    def _executor(item):
        conn = get_oracle_connection_from_item(item)
        try:
            query = sql.rstrip().rstrip(";")

            cursor = conn.cursor()
            try:
                # 生成执行计划
                cursor.execute(f"EXPLAIN PLAN FOR {query}")

                # 读取执行计划输出
                cursor.execute("SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY())")
                plan_lines = [row[0] for row in cursor.fetchall()]
            finally:
                cursor.close()

            return {
                "success": True,
                "sql": query,
                "execution_plan": plan_lines,
            }
        except oracledb.Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

    return safe_json_dumps(execute_with_credentials(normalized, _executor))
