from __future__ import annotations

from typing import Any, cast

from apps.node_mgmt.constants.installer import InstallerConstants
from apps.node_mgmt.utils.step_tracker import now_iso


"""Canonical write-path schema helpers for installer task results."""


INSTALLER_ACTION_MESSAGES = {
    "bootstrap_running": "Start installation",
    "download": "Download installer files",
    "write_config": "Write configuration",
    "install": "Install controller",
    "install_complete": "Finalize installation",
    "configure_runtime": "Configure runtime",
    "installer": "Run installer",
}


def _coerce_number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if number != number:
        return None

    return number


def _coerce_non_negative_int(value: Any) -> int | None:
    number = _coerce_number(value)
    if number is None:
        return None
    return max(int(number), 0)


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_installer_action(raw_step: Any) -> str:
    """Map raw installer step names to canonical action names."""
    normalized_step = _clean_text(raw_step)
    if not normalized_step:
        return "installer"
    return InstallerConstants.INSTALLER_EVENT_STEP_MAP.get(normalized_step, normalized_step)


def default_installer_message(action: str) -> str:
    if action in INSTALLER_ACTION_MESSAGES:
        return INSTALLER_ACTION_MESSAGES[action]
    return (action or "installer").replace("_", " ").title()


def normalize_installer_status(raw_status: Any) -> str:
    """Normalize installer step status into the canonical task-step set."""
    normalized_status = (_clean_text(raw_status) or InstallerConstants.STEP_STATUS_RUNNING).lower()
    return InstallerConstants.INSTALLER_EVENT_STATUS_MAP.get(normalized_status, InstallerConstants.STEP_STATUS_RUNNING)


def normalize_overall_status(raw_status: Any) -> str:
    """Normalize task overall status while keeping existing enum semantics."""
    normalized_status = (_clean_text(raw_status) or InstallerConstants.OVERALL_STATUS_ERROR).lower()
    allowed_statuses = {
        InstallerConstants.OVERALL_STATUS_WAITING,
        InstallerConstants.OVERALL_STATUS_RUNNING,
        InstallerConstants.OVERALL_STATUS_SUCCESS,
        InstallerConstants.OVERALL_STATUS_ERROR,
        InstallerConstants.OVERALL_STATUS_TIMEOUT,
        InstallerConstants.OVERALL_STATUS_CANCELLED,
    }
    if normalized_status in allowed_statuses:
        return normalized_status
    return InstallerConstants.OVERALL_STATUS_ERROR


def normalize_progress(percent=None, current=None, total=None, unit="bytes") -> dict:
    """Normalize progress values stored in task result details."""
    normalized_current = _coerce_non_negative_int(current)
    normalized_total = _coerce_non_negative_int(total)
    normalized_percent = _coerce_number(percent)

    if normalized_percent is None and normalized_current is not None and normalized_total:
        normalized_percent = (normalized_current / normalized_total) * 100

    if normalized_percent is not None:
        normalized_percent = max(0, min(int(round(normalized_percent)), 100))

    normalized_unit = unit if normalized_current is not None or normalized_total is not None else None

    return {
        "percent": normalized_percent,
        "current": normalized_current,
        "total": normalized_total,
        "unit": normalized_unit,
    }


def normalize_failure(message=None, error=None, details=None) -> dict | None:
    """Build the shared failure envelope used by task results and step details."""
    prepared_details = details if isinstance(details, dict) else {}
    failure_message = (
        _clean_text(message)
        or _clean_text(prepared_details.get("service_error"))
        or _clean_text(prepared_details.get("error_message"))
        or _clean_text(error)
    )
    if not failure_message:
        return None

    failure_type = _clean_text(prepared_details.get("error_type")) or "execution"
    failure_code = prepared_details.get("exit_code")
    return {
        "message": failure_message,
        "type": failure_type,
        "code": failure_code,
        "retriable": failure_type in {"timeout", "connection"},
        "raw_error": _clean_text(error),
    }


def installer_step_index(action: str) -> int | None:
    if action not in InstallerConstants.INSTALLER_STEP_SEQUENCE:
        return None
    return InstallerConstants.INSTALLER_STEP_SEQUENCE.index(action) + 1


def build_installer_event_details(event: dict[str, Any]) -> dict:
    """Build canonical details payload for one installer event line."""
    action = normalize_installer_action(event.get("step"))
    progress = normalize_progress(
        percent=event.get("progress"),
        current=event.get("downloaded_bytes"),
        total=event.get("total_bytes"),
    )
    failure = normalize_failure(
        message=event.get("message"),
        error=event.get("error"),
    )
    return {
        "installer_event": True,
        "raw_step": _clean_text(event.get("step")),
        "raw_status": _clean_text(event.get("status")),
        "step_index": installer_step_index(action),
        "step_total": len(InstallerConstants.INSTALLER_STEP_SEQUENCE),
        "progress": progress,
        "timestamp": _clean_text(event.get("timestamp")) or now_iso(),
        "error": _clean_text(event.get("error")),
        "installer_message": _clean_text(event.get("message")),
        "failure": failure,
    }


def build_installer_event_record(event: dict[str, Any]) -> dict:
    """Build canonical step payload for one installer event line."""
    action = normalize_installer_action(event.get("step"))
    status = normalize_installer_status(event.get("status"))
    details = build_installer_event_details(event)
    message = details.get("installer_message") or default_installer_message(action)
    return {
        "action": action,
        "status": status,
        "message": message,
        "timestamp": details.get("timestamp") or now_iso(),
        "details": details,
    }


def summarize_installer_progress(result: dict | None) -> dict | None:
    """Summarize the latest installer-event step for frontend progress UI."""
    if not isinstance(result, dict):
        return None

    steps = result.get("steps", [])
    if not isinstance(steps, list):
        return None

    installer_steps = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        details = step.get("details")
        if not isinstance(details, dict) or not details.get("installer_event"):
            continue
        installer_steps.append(step)

    if not installer_steps:
        return None

    latest = installer_steps[-1]
    details = latest.get("details")
    if not isinstance(details, dict):
        details = {}

    progress = details.get("progress")
    if not isinstance(progress, dict):
        progress = {}

    details = cast(dict[str, Any], details)
    progress = cast(dict[str, Any], progress)

    action = latest.get("action") or normalize_installer_action(details.get("raw_step"))

    return {
        "current_step": action,
        "current_status": normalize_installer_status(latest.get("status")),
        "current_message": latest.get("message") or details.get("installer_message") or default_installer_message(action),
        "progress": normalize_progress(
            percent=progress.get("percent"),
            current=progress.get("current"),
            total=progress.get("total"),
            unit=progress.get("unit") or "bytes",
        ),
        "step_index": details.get("step_index") or installer_step_index(action),
        "step_total": details.get("step_total") or len(InstallerConstants.INSTALLER_STEP_SEQUENCE),
    }
