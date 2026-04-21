import importlib.util
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

import pytest


class _Logger:
    def info(self, *args, **kwargs):
        return None

    def debug(self, *args, **kwargs):
        return None

    def warning(self, *args, **kwargs):
        return None

    def error(self, *args, **kwargs):
        return None


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


class _PolicyQuerySet:
    def __init__(self, manager):
        self.manager = manager

    def select_related(self, *args):
        return self

    def first(self):
        return self.manager.policy

    def update(self, **kwargs):
        self.manager.updates.append(kwargs)
        for key, value in kwargs.items():
            setattr(self.manager.policy, key, value)
        return 1


class _PolicyManager:
    def __init__(self, policy):
        self.policy = policy
        self.updates = []

    def filter(self, **kwargs):
        return _PolicyQuerySet(self)


class _PolicyModel:
    objects = None


class _FrozenDateTime(datetime):
    fixed_now = datetime(2026, 4, 21, 8, 0, tzinfo=timezone.utc)

    @classmethod
    def now(cls, tz=None):
        if tz is None:
            return cls.fixed_now.replace(tzinfo=None)
        return cls.fixed_now.astimezone(tz)


def _install_monitor_policy_dependencies(monkeypatch, policy, scan_cls):
    def shared_task(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    _PolicyModel.objects = _PolicyManager(policy)

    _install_module(monkeypatch, "celery", shared_task=shared_task)
    _install_module(monkeypatch, "celery_singleton", Singleton=object)
    _install_module(monkeypatch, "apps.core.exceptions.base_app_exception", BaseAppException=Exception)
    _install_module(monkeypatch, "apps.monitor.models", MonitorPolicy=_PolicyModel)
    _install_module(monkeypatch, "apps.core.logger", celery_logger=_Logger())
    _install_module(monkeypatch, "apps.monitor.tasks.services.policy_scan", MonitorPolicyScan=scan_cls)
    _install_module(monkeypatch, "apps.monitor.tasks.utils.policy_methods", period_to_seconds=lambda period: 60)
    _install_module(
        monkeypatch,
        "apps.monitor.constants.alert_policy",
        AlertConstants=types.SimpleNamespace(MAX_BACKFILL_SECONDS=3600, MAX_BACKFILL_COUNT=10),
    )


def test_scan_policy_task_does_not_persist_watermark_when_scan_fails(monkeypatch):
    policy = types.SimpleNamespace(
        id=1001,
        enable=True,
        last_run_time=datetime(2026, 4, 21, 7, 59, tzinfo=timezone.utc),
        period={"type": "min", "value": 1},
    )

    class FailingScan:
        def __init__(self, policy_obj):
            self.policy_obj = policy_obj

        def run(self):
            raise RuntimeError("victoriametrics unavailable")

    _install_monitor_policy_dependencies(monkeypatch, policy, FailingScan)
    module = _load_module(
        "monitor_policy_failure_test_module",
        Path(__file__).resolve().parents[1] / "tasks" / "monitor_policy.py",
    )
    module.datetime = _FrozenDateTime

    with pytest.raises(RuntimeError, match="victoriametrics unavailable"):
        module.scan_policy_task(policy.id)

    assert _PolicyModel.objects.updates == []


def test_scan_policy_task_persists_watermark_after_successful_scan(monkeypatch):
    policy = types.SimpleNamespace(
        id=1002,
        enable=True,
        last_run_time=datetime(2026, 4, 21, 7, 59, tzinfo=timezone.utc),
        period={"type": "min", "value": 1},
    )
    scanned_at = []

    class SuccessfulScan:
        def __init__(self, policy_obj):
            self.policy_obj = policy_obj

        def run(self):
            scanned_at.append(self.policy_obj.last_run_time)

    _install_monitor_policy_dependencies(monkeypatch, policy, SuccessfulScan)
    module = _load_module(
        "monitor_policy_success_test_module",
        Path(__file__).resolve().parents[1] / "tasks" / "monitor_policy.py",
    )
    module.datetime = _FrozenDateTime

    result = module.scan_policy_task(policy.id)

    assert scanned_at == [_FrozenDateTime.fixed_now]
    assert _PolicyModel.objects.updates == [{"last_run_time": _FrozenDateTime.fixed_now}]
    assert result["success"] is True


def _install_scanner_dependencies(monkeypatch):
    alert_constants = types.SimpleNamespace(THRESHOLD="threshold", NO_DATA="no_data")

    _install_module(monkeypatch, "apps.monitor.constants.alert_policy", AlertConstants=alert_constants)
    _install_module(
        monkeypatch,
        "apps.monitor.models",
        MonitorInstanceOrganization=object,
        MonitorAlert=object,
        MonitorInstance=object,
        PolicyInstanceBaseline=object,
    )
    _install_module(monkeypatch, "apps.monitor.services.policy_baseline", PolicyBaselineService=object)
    _install_module(monkeypatch, "apps.monitor.tasks.services.policy_scan.metric_query", MetricQueryService=object)
    _install_module(monkeypatch, "apps.monitor.tasks.services.policy_scan.alert_detector", AlertDetector=object)
    _install_module(monkeypatch, "apps.monitor.tasks.services.policy_scan.event_alert_manager", EventAlertManager=object)
    _install_module(monkeypatch, "apps.monitor.tasks.services.policy_scan.snapshot_recorder", SnapshotRecorder=object)
    _install_module(monkeypatch, "apps.core.logger", celery_logger=_Logger())
    return alert_constants


def test_policy_scan_collect_events_propagates_threshold_failures(monkeypatch):
    alert_constants = _install_scanner_dependencies(monkeypatch)
    module = _load_module(
        "monitor_policy_scanner_failure_test_module",
        Path(__file__).resolve().parents[1] / "tasks" / "services" / "policy_scan" / "scanner.py",
    )

    scanner = object.__new__(module.MonitorPolicyScan)
    scanner.policy = types.SimpleNamespace(id=1003, enable_alerts=[alert_constants.THRESHOLD])

    def fail_threshold():
        raise RuntimeError("metric query failed")

    scanner._process_threshold_alerts = fail_threshold

    with pytest.raises(RuntimeError, match="metric query failed"):
        scanner._collect_events()


def test_policy_scan_pre_check_propagates_metric_setup_failures(monkeypatch):
    _install_scanner_dependencies(monkeypatch)
    module = _load_module(
        "monitor_policy_scanner_precheck_test_module",
        Path(__file__).resolve().parents[1] / "tasks" / "services" / "policy_scan" / "scanner.py",
    )

    scanner = object.__new__(module.MonitorPolicyScan)
    scanner.policy = types.SimpleNamespace(id=1004, source={})
    scanner.metric_query_service = types.SimpleNamespace(set_monitor_obj_instance_key=lambda: (_ for _ in ()).throw(RuntimeError("metric missing")))

    with pytest.raises(RuntimeError, match="metric missing"):
        scanner._pre_check()


def test_no_data_events_can_notify_without_legacy_policy_field(monkeypatch):
    bulk_update_calls = []

    class MonitorEvent:
        class objects:
            @staticmethod
            def bulk_update(event_objs, fields, batch_size=None):
                bulk_update_calls.append((event_objs, fields, batch_size))

    _install_module(
        monkeypatch,
        "apps.monitor.constants.alert_policy",
        AlertConstants=types.SimpleNamespace(),
    )
    _install_module(
        monkeypatch,
        "apps.monitor.constants.database",
        DatabaseConstants=types.SimpleNamespace(BULK_UPDATE_BATCH_SIZE=100),
    )
    _install_module(
        monkeypatch,
        "apps.monitor.models",
        MonitorAlert=object,
        MonitorEvent=MonitorEvent,
        MonitorEventRawData=object,
    )
    _install_module(
        monkeypatch,
        "apps.monitor.utils.dimension",
        format_dimension_str=lambda dimensions: "",
    )
    _install_module(
        monkeypatch,
        "apps.monitor.utils.system_mgmt_api",
        SystemMgmtUtils=object,
    )
    _install_module(monkeypatch, "apps.system_mgmt.models", Channel=object)
    _install_module(monkeypatch, "apps.core.logger", celery_logger=_Logger())

    module = _load_module(
        "monitor_policy_event_alert_manager_test_module",
        Path(__file__).resolve().parents[1] / "tasks" / "services" / "policy_scan" / "event_alert_manager.py",
    )

    manager = object.__new__(module.EventAlertManager)
    manager.policy = types.SimpleNamespace(id=1005, name="no-data-policy")
    manager._is_alert_center = False
    manager.send_notice = lambda event: [{"result": True}]

    event = types.SimpleNamespace(level="no_data", notice_result=None)

    manager.notify_events([event])

    assert event.notice_result == [{"result": True}]
    assert bulk_update_calls == [([event], ["notice_result"], 100)]


def test_threshold_event_does_not_reuse_active_no_data_alert(monkeypatch):
    _install_module(
        monkeypatch,
        "apps.monitor.constants.alert_policy",
        AlertConstants=types.SimpleNamespace(),
    )
    _install_module(
        monkeypatch,
        "apps.monitor.constants.database",
        DatabaseConstants=types.SimpleNamespace(
            BULK_CREATE_BATCH_SIZE=100,
            BULK_UPDATE_BATCH_SIZE=100,
        ),
    )
    _install_module(
        monkeypatch,
        "apps.monitor.models",
        MonitorAlert=object,
        MonitorEvent=object,
        MonitorEventRawData=object,
    )
    _install_module(
        monkeypatch,
        "apps.monitor.utils.dimension",
        format_dimension_str=lambda dimensions: "",
    )
    _install_module(
        monkeypatch,
        "apps.monitor.utils.system_mgmt_api",
        SystemMgmtUtils=object,
    )
    _install_module(monkeypatch, "apps.system_mgmt.models", Channel=object)
    _install_module(monkeypatch, "apps.core.logger", celery_logger=_Logger())

    module = _load_module(
        "monitor_policy_event_alert_manager_key_test_module",
        Path(__file__).resolve().parents[1]
        / "tasks"
        / "services"
        / "policy_scan"
        / "event_alert_manager.py",
    )

    metric_instance_id = "('host-1',)"
    active_no_data_alert = types.SimpleNamespace(
        id=101,
        metric_instance_id=metric_instance_id,
        monitor_instance_id="host-1",
        alert_type="no_data",
    )
    created_alert = types.SimpleNamespace(
        id=202,
        metric_instance_id=metric_instance_id,
        alert_type="alert",
    )
    created_from_events = []
    persisted_events = []
    existing_updates = []

    manager = object.__new__(module.EventAlertManager)
    manager.policy = types.SimpleNamespace(id=1006, name="mixed-policy")
    manager.active_alerts = [active_no_data_alert]
    manager._create_alerts_from_events = lambda events: created_from_events.extend(
        events
    ) or [created_alert]
    manager.create_events = lambda events: persisted_events.extend(events) or events
    manager._update_existing_alerts_from_events = lambda events: existing_updates.extend(
        events
    )

    threshold_event = {
        "metric_instance_id": metric_instance_id,
        "monitor_instance_id": "host-1",
        "dimensions": {"instance_id": "host-1"},
        "value": 95.0,
        "level": "critical",
        "content": "cpu critical",
    }

    event_objs, new_alerts = manager.create_events_and_alerts([threshold_event])

    assert created_from_events == [threshold_event]
    assert persisted_events == [threshold_event]
    assert existing_updates == []
    assert threshold_event["alert_id"] == created_alert.id
    assert threshold_event["_alert_obj"] is created_alert
    assert event_objs == [threshold_event]
    assert new_alerts == [created_alert]


def test_send_notice_returns_channel_result_for_event_audit(monkeypatch):
    send_results = [{"result": True, "message": "sent"}]

    _install_module(
        monkeypatch,
        "apps.monitor.constants.alert_policy",
        AlertConstants=types.SimpleNamespace(),
    )
    _install_module(
        monkeypatch,
        "apps.monitor.constants.database",
        DatabaseConstants=types.SimpleNamespace(),
    )
    _install_module(
        monkeypatch,
        "apps.monitor.models",
        MonitorAlert=object,
        MonitorEvent=object,
        MonitorEventRawData=object,
    )
    _install_module(
        monkeypatch,
        "apps.monitor.utils.dimension",
        format_dimension_str=lambda dimensions: "",
    )
    _install_module(
        monkeypatch,
        "apps.monitor.utils.system_mgmt_api",
        SystemMgmtUtils=types.SimpleNamespace(
            send_msg_with_channel=lambda *args: send_results[0]
        ),
    )
    _install_module(monkeypatch, "apps.system_mgmt.models", Channel=object)
    _install_module(monkeypatch, "apps.core.logger", celery_logger=_Logger())

    module = _load_module(
        "monitor_policy_event_alert_manager_notice_test_module",
        Path(__file__).resolve().parents[1]
        / "tasks"
        / "services"
        / "policy_scan"
        / "event_alert_manager.py",
    )

    manager = object.__new__(module.EventAlertManager)
    manager.policy = types.SimpleNamespace(
        id=1007,
        name="notice-policy",
        notice_type_id=9,
        notice_users=["admin"],
    )
    event = types.SimpleNamespace(content="cpu critical")

    assert manager.send_notice(event) == send_results
