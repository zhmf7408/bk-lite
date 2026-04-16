from __future__ import annotations

from typing import Any

from apps.node_mgmt.utils.installer_schema import normalize_failure, normalize_overall_status


"""Shared normalization helpers for generic task result envelopes."""


def _extract_latest_failure_from_steps(steps):
    """Return the most recent normalized failure stored in step details."""
    if not isinstance(steps, list):
        return None

    for step in reversed(steps):
        if not isinstance(step, dict):
            continue
        details = step.get("details")
        if isinstance(details, dict) and details.get("failure"):
            return details.get("failure")

    return None


def _normalize_step_message(step_message):
    if isinstance(step_message, str):
        stripped_message = step_message.strip()
        if stripped_message:
            return step_message
    return "--"


def normalize_task_details(details=None, *, message=None, error=None):
    """Preserve legacy detail keys while attaching normalized failure data."""
    prepared_details = details.copy() if isinstance(details, dict) else {}
    failure = normalize_failure(message=message, error=error, details=prepared_details)
    if failure:
        prepared_details["failure"] = failure
        if failure.get("type") == "timeout":
            prepared_details["timeout"] = True
    return prepared_details or None


def apply_result_envelope(result=None, *, overall_status=None, final_message=None, failure=None):
    """Guarantee top-level task result fields and normalized terminal failure."""
    prepared_result = result.copy() if isinstance(result, dict) else {}
    steps = prepared_result.get("steps")
    prepared_result["steps"] = steps if isinstance(steps, list) else []

    if overall_status is not None:
        prepared_result["overall_status"] = normalize_overall_status(overall_status)

    if final_message is not None:
        prepared_result["final_message"] = final_message

    normalized_failure = normalize_failure(
        message=(failure or {}).get("message") if isinstance(failure, dict) else None,
        error=(failure or {}).get("raw_error") if isinstance(failure, dict) else None,
        details=failure,
    )

    current_status = prepared_result.get("overall_status")
    if current_status in {"error", "timeout", "cancelled"} and normalized_failure:
        prepared_result["failure"] = normalized_failure
    elif current_status == "success":
        prepared_result.pop("failure", None)

    return prepared_result


def normalize_task_result_for_read(result=None):
    """Normalize historical task result payloads before returning them to readers."""
    prepared_result = apply_result_envelope(
        result,
        overall_status=(result or {}).get("overall_status") if isinstance(result, dict) else None,
        final_message=(result or {}).get("final_message") if isinstance(result, dict) else None,
        failure=(result or {}).get("failure") if isinstance(result, dict) else None,
    )

    steps = prepared_result.get("steps", [])
    normalized_steps = []
    latest_failure = None

    for step in steps:
        if not isinstance(step, dict):
            continue

        step_details_raw = step.get("details") if isinstance(step.get("details"), dict) else None
        step_status = step.get("status") or "waiting"
        step_message = _normalize_step_message(step.get("message"))
        should_attach_failure = step_status in {"error", "timeout"} or (step_details_raw or {}).get("error_type") == "timeout"
        step_details = normalize_task_details(
            step_details_raw,
            message=step_message if should_attach_failure else None,
            error=step_details_raw.get("error") if step_details_raw else None,
        )

        normalized_step = {
            "action": step.get("action") or "unknown",
            "status": step_status,
            "message": step_message,
            "timestamp": step.get("timestamp") or "",
        }
        if step_details:
            normalized_step["details"] = step_details
            if step_details.get("failure"):
                latest_failure = step_details.get("failure")

        normalized_steps.append(normalized_step)

    prepared_result["steps"] = normalized_steps

    installer_progress = prepared_result.get("installer_progress")
    if not isinstance(installer_progress, dict):
        prepared_result["installer_progress"] = None

    latest_failure = latest_failure or _extract_latest_failure_from_steps(prepared_result.get("steps"))

    if latest_failure and prepared_result.get("overall_status") in {"error", "timeout", "cancelled"}:
        prepared_result["failure"] = latest_failure

    return prepared_result
