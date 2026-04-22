from apps.core.utils.loader import LanguageLoader
from apps.opspilot.metis.llm.tools.mssql import CONSTRUCTOR_PARAMS as MSSQL_CONSTRUCTOR_PARAMS, __all__ as MSSQL_EXPORTS
from apps.opspilot.metis.llm.tools.mssql.connection import get_mssql_instances_prompt
from apps.opspilot.metis.llm.tools.mysql import CONSTRUCTOR_PARAMS as MYSQL_CONSTRUCTOR_PARAMS, __all__ as MYSQL_EXPORTS
from apps.opspilot.metis.llm.tools.mysql.connection import get_mysql_instances_prompt
from apps.opspilot.metis.llm.tools.oracle import CONSTRUCTOR_PARAMS as ORACLE_CONSTRUCTOR_PARAMS, __all__ as ORACLE_EXPORTS
from apps.opspilot.metis.llm.tools.oracle.connection import get_oracle_instances_prompt
from apps.opspilot.metis.llm.tools.redis import CONSTRUCTOR_PARAMS as REDIS_CONSTRUCTOR_PARAMS, __all__ as REDIS_EXPORTS
from apps.opspilot.metis.llm.tools.redis.connection import get_redis_instances_prompt

BUILTIN_REDIS_TOOL_ID = -1
BUILTIN_REDIS_TOOL_NAME = "redis"

BUILTIN_MYSQL_TOOL_ID = -2
BUILTIN_MYSQL_TOOL_NAME = "mysql"

BUILTIN_ORACLE_TOOL_ID = -3
BUILTIN_ORACLE_TOOL_NAME = "oracle"

BUILTIN_MSSQL_TOOL_ID = -4
BUILTIN_MSSQL_TOOL_NAME = "mssql"


def _build_kwargs_from_params(constructor_params):
    return [
        {
            "key": item["name"],
            "value": "",
            "type": item["type"],
            "isRequired": item["required"],
            "description": item["description"],
        }
        for item in constructor_params
    ]


def _build_sub_tools(tool_name, exports, loader: LanguageLoader):
    sub_tools = []
    for name in exports:
        if name == "CONSTRUCTOR_PARAMS":
            continue
        sub_tools.append(
            {
                "name": name,
                "description": loader.get(f"tools.{tool_name}.tools.{name}.description") or "",
            }
        )
    return sub_tools


def build_builtin_redis_tool(loader: LanguageLoader):
    description = loader.get(f"tools.{BUILTIN_REDIS_TOOL_NAME}.description") or "Redis built-in tool"
    return {
        "id": BUILTIN_REDIS_TOOL_ID,
        "name": BUILTIN_REDIS_TOOL_NAME,
        "display_name": "Redis",
        "description": description,
        "description_tr": description,
        "icon": "gongjuji",
        "team": [],
        "tags": [],
        "params": {
            "name": BUILTIN_REDIS_TOOL_NAME,
            "url": f"langchain:{BUILTIN_REDIS_TOOL_NAME}",
            "kwargs": _build_kwargs_from_params(REDIS_CONSTRUCTOR_PARAMS),
            "enable_auth": False,
            "auth_token": "",
        },
        "is_build_in": True,
        "tools": _build_sub_tools(BUILTIN_REDIS_TOOL_NAME, REDIS_EXPORTS, loader),
    }


def build_builtin_redis_runtime_tool(tool_kwargs):
    return {
        "name": BUILTIN_REDIS_TOOL_NAME,
        "url": f"langchain:{BUILTIN_REDIS_TOOL_NAME}",
        "enable_auth": False,
        "auth_token": "",
        "extra_tools_prompt": get_redis_instances_prompt(tool_kwargs),
    }


def build_builtin_mysql_tool(loader: LanguageLoader):
    description = loader.get(f"tools.{BUILTIN_MYSQL_TOOL_NAME}.description") or "MySQL built-in tool"
    return {
        "id": BUILTIN_MYSQL_TOOL_ID,
        "name": BUILTIN_MYSQL_TOOL_NAME,
        "display_name": "MySQL",
        "description": description,
        "description_tr": description,
        "icon": "gongjuji",
        "team": [],
        "tags": [],
        "params": {
            "name": BUILTIN_MYSQL_TOOL_NAME,
            "url": f"langchain:{BUILTIN_MYSQL_TOOL_NAME}",
            "kwargs": _build_kwargs_from_params(MYSQL_CONSTRUCTOR_PARAMS),
            "enable_auth": False,
            "auth_token": "",
        },
        "is_build_in": True,
        "tools": _build_sub_tools(BUILTIN_MYSQL_TOOL_NAME, MYSQL_EXPORTS, loader),
    }


def build_builtin_mysql_runtime_tool(tool_kwargs):
    return {
        "name": BUILTIN_MYSQL_TOOL_NAME,
        "url": f"langchain:{BUILTIN_MYSQL_TOOL_NAME}",
        "enable_auth": False,
        "auth_token": "",
        "extra_tools_prompt": get_mysql_instances_prompt(tool_kwargs),
    }


def build_builtin_oracle_tool(loader: LanguageLoader):
    description = loader.get(f"tools.{BUILTIN_ORACLE_TOOL_NAME}.description") or "Oracle built-in tool"
    return {
        "id": BUILTIN_ORACLE_TOOL_ID,
        "name": BUILTIN_ORACLE_TOOL_NAME,
        "display_name": "Oracle",
        "description": description,
        "description_tr": description,
        "icon": "gongjuji",
        "team": [],
        "tags": [],
        "params": {
            "name": BUILTIN_ORACLE_TOOL_NAME,
            "url": f"langchain:{BUILTIN_ORACLE_TOOL_NAME}",
            "kwargs": _build_kwargs_from_params(ORACLE_CONSTRUCTOR_PARAMS),
            "enable_auth": False,
            "auth_token": "",
        },
        "is_build_in": True,
        "tools": _build_sub_tools(BUILTIN_ORACLE_TOOL_NAME, ORACLE_EXPORTS, loader),
    }


def build_builtin_oracle_runtime_tool(tool_kwargs):
    return {
        "name": BUILTIN_ORACLE_TOOL_NAME,
        "url": f"langchain:{BUILTIN_ORACLE_TOOL_NAME}",
        "enable_auth": False,
        "auth_token": "",
        "extra_tools_prompt": get_oracle_instances_prompt(tool_kwargs),
    }


def build_builtin_mssql_tool(loader: LanguageLoader):
    description = loader.get(f"tools.{BUILTIN_MSSQL_TOOL_NAME}.description") or "MSSQL built-in tool"
    return {
        "id": BUILTIN_MSSQL_TOOL_ID,
        "name": BUILTIN_MSSQL_TOOL_NAME,
        "display_name": "MSSQL",
        "description": description,
        "description_tr": description,
        "icon": "gongjuji",
        "team": [],
        "tags": [],
        "params": {
            "name": BUILTIN_MSSQL_TOOL_NAME,
            "url": f"langchain:{BUILTIN_MSSQL_TOOL_NAME}",
            "kwargs": _build_kwargs_from_params(MSSQL_CONSTRUCTOR_PARAMS),
            "enable_auth": False,
            "auth_token": "",
        },
        "is_build_in": True,
        "tools": _build_sub_tools(BUILTIN_MSSQL_TOOL_NAME, MSSQL_EXPORTS, loader),
    }


def build_builtin_mssql_runtime_tool(tool_kwargs):
    return {
        "name": BUILTIN_MSSQL_TOOL_NAME,
        "url": f"langchain:{BUILTIN_MSSQL_TOOL_NAME}",
        "enable_auth": False,
        "auth_token": "",
        "extra_tools_prompt": get_mssql_instances_prompt(tool_kwargs),
    }
