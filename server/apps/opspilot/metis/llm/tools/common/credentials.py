from typing import Any, Callable, Dict, List, Literal, Optional, Protocol, TypedDict, runtime_checkable


class CredentialError(Exception):
    pass


class CredentialValidationError(CredentialError):
    pass


class CredentialConflictError(CredentialError):
    pass


class CredentialItem(TypedDict):
    index: int
    name: str
    raw: Dict[str, Any]
    config: Dict[str, Any]


class NormalizedCredentials(TypedDict):
    mode: Literal["single", "multi"]
    legacy_single: bool
    items: List[CredentialItem]


@runtime_checkable
class CredentialAdapter(Protocol):
    flat_fields: List[str]

    def build_from_flat_config(self, configurable: Dict[str, Any]) -> Dict[str, Any]: ...
    def build_from_credential_item(self, item: Dict[str, Any]) -> Dict[str, Any]: ...
    def validate(self, config: Dict[str, Any]) -> None: ...
    def get_display_name(self, source: Dict[str, Any], index: int) -> str: ...


def normalize_credentials(configurable: Dict[str, Any], adapter: CredentialAdapter) -> NormalizedCredentials:
    """
    Normalize credentials from configurable dict.

    Priority:
    1. 'credentials' list key (new multi-mode)
    2. flat fields (legacy single-mode)

    Raises CredentialConflictError if both 'credentials' and flat fields are present.
    Raises CredentialValidationError if 'credentials' is empty or invalid.
    """
    credentials = configurable.get("credentials")
    has_flat = any(configurable.get(f) for f in adapter.flat_fields)

    if credentials is not None and has_flat:
        raise CredentialConflictError(
            "Cannot use both 'credentials' list and flat credential fields at the same time"
        )

    if credentials is not None:
        if not isinstance(credentials, list) or len(credentials) == 0:
            raise CredentialValidationError("'credentials' must be a non-empty list")
        items: List[CredentialItem] = []
        for i, cred in enumerate(credentials):
            if not isinstance(cred, dict):
                raise CredentialValidationError(f"Each credential item must be a dict, got {type(cred)} at index {i}")
            config = adapter.build_from_credential_item(cred)
            adapter.validate(config)
            items.append(CredentialItem(
                index=i,
                name=adapter.get_display_name(cred, i),
                raw=cred,
                config=config,
            ))
        mode: Literal["single", "multi"] = "single" if len(items) == 1 else "multi"
        return NormalizedCredentials(mode=mode, legacy_single=False, items=items)

    # Legacy single-mode
    config = adapter.build_from_flat_config(configurable)
    adapter.validate(config)
    return NormalizedCredentials(
        mode="single",
        legacy_single=True,
        items=[CredentialItem(
            index=0,
            name=adapter.get_display_name(configurable, 0),
            raw=configurable,
            config=config,
        )],
    )


def execute_with_credentials(
    normalized: NormalizedCredentials,
    executor: Callable[[CredentialItem], Any],
    unwrap_single: bool = True,
) -> Any:
    """
    Execute executor for each credential item.

    Single mode (unwrap_single=True): returns the executor result directly.
    Multi mode: returns aggregated result with success/failure per target.
    """
    if normalized["mode"] == "single" and unwrap_single:
        return executor(normalized["items"][0])

    results = []
    for item in normalized["items"]:
        try:
            data = executor(item)
            results.append({"target": item["name"], "ok": True, "data": data})
        except Exception as e:
            results.append({"target": item["name"], "ok": False, "error": str(e)})

    succeeded = sum(1 for r in results if r["ok"])
    return {
        "mode": "multi",
        "total": len(results),
        "succeeded": succeeded,
        "failed": len(results) - succeeded,
        "results": results,
    }
