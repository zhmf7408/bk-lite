from apps.core.utils.loader import LanguageLoader
from apps.opspilot.metis.llm.tools.redis import CONSTRUCTOR_PARAMS, __all__ as REDIS_EXPORTS
from apps.opspilot.metis.llm.tools.redis.connection import get_redis_instances_prompt

BUILTIN_REDIS_TOOL_ID = -1
BUILTIN_REDIS_TOOL_NAME = "redis"


def _build_redis_kwargs():
    return [
        {
            "key": item["name"],
            "value": "",
            "type": item["type"],
            "isRequired": item["required"],
            "description": item["description"],
        }
        for item in CONSTRUCTOR_PARAMS
    ]


def _build_redis_sub_tools(loader: LanguageLoader):
    sub_tools = []
    for tool_name in REDIS_EXPORTS:
        if tool_name == "CONSTRUCTOR_PARAMS":
            continue
        sub_tools.append(
            {
                "name": tool_name,
                "description": loader.get(f"tools.{BUILTIN_REDIS_TOOL_NAME}.tools.{tool_name}.description") or "",
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
            "kwargs": _build_redis_kwargs(),
            "enable_auth": False,
            "auth_token": "",
        },
        "is_build_in": True,
        "tools": _build_redis_sub_tools(loader),
    }


def build_builtin_redis_runtime_tool(tool_kwargs):
    return {
        "name": BUILTIN_REDIS_TOOL_NAME,
        "url": f"langchain:{BUILTIN_REDIS_TOOL_NAME}",
        "enable_auth": False,
        "auth_token": "",
        "extra_tools_prompt": get_redis_instances_prompt(tool_kwargs),
    }
