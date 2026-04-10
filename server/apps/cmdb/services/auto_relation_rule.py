import json
import uuid
from dataclasses import dataclass
from typing import Any

from apps.core.exceptions.base_app_exception import BaseAppException


AUTO_RELATION_RULE_FIELD = "auto_relation_rule"
AUTO_RELATION_RULE_UNSUPPORTED_ATTR_TYPES = {
    "enum",
    "tag",
    "table",
    "organization",
    "user",
}


@dataclass(slots=True, frozen=True)
class AutoRelationMatchPair:
    src_field_id: str
    dst_field_id: str


@dataclass(slots=True, frozen=True)
class AutoRelationRule:
    rule_id: str
    enabled: bool
    match_pairs: list[AutoRelationMatchPair]
    updated_by: str = ""
    updated_at: str = ""


@dataclass(slots=True, frozen=True)
class AutoRelationRuleSet:
    version: int
    rules: list[AutoRelationRule]


def _normalize_field_id(value: Any) -> str:
    return str(value or "").strip()


def _build_match_pairs(raw_pairs: list[Any], raise_on_invalid: bool = False) -> list[AutoRelationMatchPair]:
    match_pairs: list[AutoRelationMatchPair] = []
    seen_pairs: set[tuple[str, str]] = set()

    for item in raw_pairs:
        if not isinstance(item, dict):
            if raise_on_invalid:
                raise BaseAppException("match_pairs 配置项不合法")
            continue

        src_field_id = _normalize_field_id(item.get("src_field_id"))
        dst_field_id = _normalize_field_id(item.get("dst_field_id"))
        if not src_field_id or not dst_field_id:
            if raise_on_invalid:
                raise BaseAppException("字段匹配对不能为空")
            continue

        pair_key = (src_field_id, dst_field_id)
        if pair_key in seen_pairs:
            if raise_on_invalid:
                raise BaseAppException("match_pairs 中存在重复字段匹配对")
            continue

        seen_pairs.add(pair_key)
        match_pairs.append(
            AutoRelationMatchPair(
                src_field_id=src_field_id,
                dst_field_id=dst_field_id,
            )
        )

    return match_pairs


def parse_auto_relation_rule_set(raw: str | dict[str, Any] | None) -> AutoRelationRuleSet | None:
    if raw in (None, "", {}, []):
        return None

    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, json.JSONDecodeError):
        return None

    if not isinstance(data, dict):
        return None

    raw_rules = data.get("rules") or []
    if not isinstance(raw_rules, list):
        return None

    rules: list[AutoRelationRule] = []
    for item in raw_rules:
        if not isinstance(item, dict):
            continue
        rule_id = str(item.get("rule_id") or "").strip()
        if not rule_id:
            continue
        match_pairs = _build_match_pairs(list(item.get("match_pairs") or []))
        if not match_pairs:
            continue

        rules.append(
            AutoRelationRule(
                rule_id=rule_id,
                enabled=bool(item.get("enabled", True)),
                match_pairs=match_pairs,
                updated_by=str(item.get("updated_by") or ""),
                updated_at=str(item.get("updated_at") or ""),
            )
        )

    if not rules:
        return None

    return AutoRelationRuleSet(
        version=int(data.get("version") or 2),
        rules=rules,
    )


def parse_auto_relation_rule(raw: str | dict[str, Any] | None) -> AutoRelationRule | None:
    rule_set = parse_auto_relation_rule_set(raw)
    if not rule_set or not rule_set.rules:
        return None
    return rule_set.rules[0]


def _serialize_rule(rule: AutoRelationRule) -> dict[str, Any]:
    return {
        "rule_id": rule.rule_id,
        "enabled": bool(rule.enabled),
        "match_pairs": [
            {
                "src_field_id": pair.src_field_id,
                "dst_field_id": pair.dst_field_id,
            }
            for pair in rule.match_pairs
        ],
        "updated_by": rule.updated_by,
        "updated_at": rule.updated_at,
    }


def dump_auto_relation_rule(rule: AutoRelationRule | None) -> str:
    if not rule:
        return ""
    return dump_auto_relation_rule_set(AutoRelationRuleSet(version=2, rules=[rule]))


def dump_auto_relation_rule_set(rule_set: AutoRelationRuleSet | None) -> str:
    if not rule_set or not rule_set.rules:
        return ""
    return json.dumps(
        {
            "version": int(rule_set.version or 2),
            "rules": [_serialize_rule(rule) for rule in rule_set.rules],
        },
        ensure_ascii=False,
    )


def validate_auto_relation_rule_payload(
    model_association: dict[str, Any],
    src_attrs: list[dict[str, Any]],
    dst_attrs: list[dict[str, Any]],
    payload: dict[str, Any],
) -> AutoRelationRule:
    if not isinstance(payload, dict):
        raise BaseAppException("自动关联规则配置不合法")

    raw_pairs = payload.get("match_pairs") or []
    if not isinstance(raw_pairs, list) or not raw_pairs:
        raise BaseAppException("match_pairs 不能为空")

    src_attr_map = {
        str(attr.get("attr_id") or ""): attr
        for attr in src_attrs
        if isinstance(attr, dict)
        and attr.get("attr_id")
        and not attr.get("is_display_field")
    }
    dst_attr_map = {
        str(attr.get("attr_id") or ""): attr
        for attr in dst_attrs
        if isinstance(attr, dict)
        and attr.get("attr_id")
        and not attr.get("is_display_field")
    }

    match_pairs = _build_match_pairs(raw_pairs, raise_on_invalid=True)

    for pair in match_pairs:
        src_attr = src_attr_map.get(pair.src_field_id)
        if not src_attr:
            raise BaseAppException(f"源字段 {pair.src_field_id} 不存在")
        dst_attr = dst_attr_map.get(pair.dst_field_id)
        if not dst_attr:
            raise BaseAppException(f"目标字段 {pair.dst_field_id} 不存在")

        src_attr_type = str(src_attr.get("attr_type") or "")
        dst_attr_type = str(dst_attr.get("attr_type") or "")
        if src_attr_type != dst_attr_type:
            raise BaseAppException("源字段和目标字段类型不一致")
        if src_attr_type in AUTO_RELATION_RULE_UNSUPPORTED_ATTR_TYPES:
            raise BaseAppException(f"字段类型 {src_attr_type} 不支持自动关联")

    if not match_pairs:
        raise BaseAppException("至少配置一个字段匹配对")

    return AutoRelationRule(
        rule_id=str(payload.get("rule_id") or uuid.uuid4().hex),
        enabled=bool(payload.get("enabled", True)),
        match_pairs=match_pairs,
        updated_by=str(payload.get("updated_by") or ""),
        updated_at=str(payload.get("updated_at") or ""),
    )


def build_auto_relation_rule_response(
    association: dict[str, Any],
    rule: AutoRelationRule | None,
) -> dict[str, Any]:
    result = dict(association)
    result["rule_id"] = rule.rule_id if rule else ""
    result[AUTO_RELATION_RULE_FIELD] = {
        "rule_id": rule.rule_id,
        "enabled": bool(rule.enabled),
        "match_pairs": [
            {
                "src_field_id": pair.src_field_id,
                "dst_field_id": pair.dst_field_id,
            }
            for pair in rule.match_pairs
        ],
        "updated_by": rule.updated_by,
        "updated_at": rule.updated_at,
    } if rule else None
    return result
