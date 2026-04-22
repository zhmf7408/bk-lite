import importlib.util
import sys
import types
from pathlib import Path


def _install_module(monkeypatch, name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    monkeypatch.setitem(sys.modules, name, module)
    return module


def _load_module(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_node_mgmt_view(monkeypatch):
    class ViewSet:
        pass

    def action(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    _install_module(monkeypatch, "rest_framework.viewsets", ViewSet=ViewSet)
    _install_module(monkeypatch, "rest_framework.decorators", action=action)
    _install_module(monkeypatch, "apps.core.exceptions.base_app_exception", BaseAppException=Exception)
    _install_module(monkeypatch, "apps.core.utils.web_utils", WebUtils=types.SimpleNamespace(response_success=lambda data=None: data))
    _install_module(monkeypatch, "apps.monitor.services.node_mgmt", InstanceConfigService=object)
    _install_module(monkeypatch, "apps.rpc.node_mgmt", NodeMgmt=object)
    _install_module(monkeypatch, "apps.core.logger", monitor_logger=types.SimpleNamespace(debug=lambda *args, **kwargs: None))
    _install_module(monkeypatch, "apps.monitor.utils.pagination", parse_page_params=lambda *args, **kwargs: (1, 10))

    return _load_module(
        "monitor_node_mgmt_view_test_module",
        Path(__file__).resolve().parents[1] / "views" / "node_mgmt.py",
    )


def test_build_actor_context_accepts_api_secret_integer_group_list(monkeypatch):
    module = _load_node_mgmt_view(monkeypatch)
    request = types.SimpleNamespace(
        COOKIES={"current_team": "7", "include_children": "1"},
        user=types.SimpleNamespace(
            username="api-user",
            domain="domain.com",
            is_superuser=False,
            group_list=[7],
        ),
    )

    assert module._build_actor_context(request)["group_list"] == [7]


def test_build_actor_context_keeps_token_group_dicts(monkeypatch):
    module = _load_node_mgmt_view(monkeypatch)
    request = types.SimpleNamespace(
        COOKIES={"current_team": "8"},
        user=types.SimpleNamespace(
            username="token-user",
            domain="domain.com",
            is_superuser=False,
            group_list=[{"id": "8", "name": "team-a"}],
        ),
    )

    assert module._build_actor_context(request)["group_list"] == [8]
