"""MySQL通用工具函数"""

import json
import re

from langchain_core.runnables import RunnableConfig
from loguru import logger
from mysql.connector import Error


def prepare_context(config: RunnableConfig = None) -> dict:
    """
    准备MySQL连接上下文

    从config中提取数据库连接参数,返回连接配置字典

    Args:
        config: RunnableConfig对象,包含配置参数

    Returns:
        dict: 数据库连接配置
    """
    if config is None:
        config = {}

    configurable = config.get("configurable", {}) if isinstance(config, dict) else getattr(config, "configurable", {})

    db_config = {
        "host": configurable.get("host", "localhost"),
        "port": configurable.get("port", 3306),
        "database": configurable.get("database", ""),
        "user": configurable.get("user", "root"),
        "password": configurable.get("password", ""),
    }

    return db_config


def execute_readonly_query(conn, query: str, params: tuple = None) -> list:
    """
    安全执行只读查询

    Args:
        conn: MySQL连接对象(调用方管理生命周期)
        query: SQL查询语句
        params: 查询参数(用于参数化查询),使用%s作为占位符

    Returns:
        list: 查询结果(字典列表)
    """
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SET SESSION TRANSACTION READ ONLY")
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    except Error as e:
        logger.error(f"查询执行失败: {e}")
        raise
    finally:
        if cursor:
            cursor.close()


def validate_sql_safety(sql: str) -> tuple[bool, str]:
    """
    验证SQL语句的安全性

    Args:
        sql: 待验证的SQL语句

    Returns:
        tuple: (是否安全, 错误信息)
    """
    sql_lower = sql.lower().strip()

    # 必须以SELECT或WITH开头
    if not sql_lower.startswith("select") and not sql_lower.startswith("with"):
        return False, "SQL必须以SELECT或WITH开头"

    # 禁止的关键字列表
    forbidden_keywords = [
        # 通用写操作
        "drop",
        "alter",
        "truncate",
        "create",
        "grant",
        "revoke",
        "insert",
        "update",
        "delete",
        # MySQL特有
        "load",
        "handler",
        "flush",
        "purge",
        "reset",
        "change",
        "install",
        "uninstall",
        "prepare",
        "execute",
        "deallocate",
        "kill",
        "lock",
        "unlock",
    ]

    for keyword in forbidden_keywords:
        pattern = r"\b" + keyword + r"\b"
        if re.search(pattern, sql_lower):
            return False, f"SQL包含禁止的关键字: {keyword}"

    # 禁止注释注入
    if "--" in sql or "/*" in sql:
        return False, "SQL不允许包含注释符号"

    # 禁止分号分隔的多条语句
    if sql.count(";") > 1 or (sql.count(";") == 1 and not sql.strip().endswith(";")):
        return False, "禁止执行多条SQL语句"

    return True, ""


def format_size(bytes_value) -> str:
    """
    格式化字节大小为可读格式

    Args:
        bytes_value: 字节数

    Returns:
        str: 格式化后的大小字符串(如 "1.50 GB")
    """
    if bytes_value is None:
        return "0 B"

    bytes_value = int(bytes_value)

    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0

    return f"{bytes_value:.2f} EB"


def format_duration(milliseconds) -> str:
    """
    格式化时间为可读格式

    Args:
        milliseconds: 毫秒数

    Returns:
        str: 格式化后的时间字符串(如 "1.50s", "200.00ms")
    """
    if milliseconds is None:
        return "0ms"

    milliseconds = float(milliseconds)

    if milliseconds < 1:
        return f"{milliseconds * 1000:.2f}μs"
    elif milliseconds < 1000:
        return f"{milliseconds:.2f}ms"
    elif milliseconds < 60000:
        return f"{milliseconds / 1000:.2f}s"
    elif milliseconds < 3600000:
        return f"{milliseconds / 60000:.2f}min"
    else:
        return f"{milliseconds / 3600000:.2f}h"


def parse_mysql_version(conn) -> dict:
    """
    解析MySQL版本信息

    Args:
        conn: MySQL连接对象

    Returns:
        dict: 版本信息,包含 full_version 和 major_version
    """
    try:
        result = execute_readonly_query(conn, "SELECT VERSION() as version")
        version_string = result[0]["version"]
        major_version = int(version_string.split(".")[0]) if version_string else 0
        return {"full_version": version_string, "major_version": major_version}
    except Exception as e:
        logger.error(f"解析版本失败: {e}")
        return {"full_version": "unknown", "major_version": 0}


def safe_json_dumps(data) -> str:
    """
    安全的JSON序列化,处理特殊类型

    Args:
        data: 要序列化的数据

    Returns:
        str: JSON字符串
    """

    def default_handler(obj):
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return str(obj)

    return json.dumps(data, default=default_handler, ensure_ascii=False, indent=2)


def calculate_percentage(part: float, total: float) -> float:
    """
    计算百分比

    Args:
        part: 部分值
        total: 总值

    Returns:
        float: 百分比(0-100)
    """
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)
