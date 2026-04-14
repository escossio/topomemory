#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from typing import Any

SEMANTIC_PROFILE_VERSION = "semantic-profile-v1"
SEMANTIC_PROFILE_VARIANT_ENV = "TOPOMEMORY_SEMANTIC_PROFILE_VARIANT"
DEFAULT_SEMANTIC_PROFILE_VARIANT = "control"


def format_value(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    text = str(value).strip()
    return text if text else "none"


def split_tokens(value: str | None) -> list[str]:
    if not value:
        return []
    tokens: list[str] = []
    for raw in str(value).replace(".", " ").replace("-", " ").replace("_", " ").split():
        cleaned = "".join(ch for ch in raw.lower() if ch.isalnum())
        if cleaned:
            tokens.append(cleaned)
    return tokens


def normalize_variant(value: str | None) -> str:
    variant = (value or DEFAULT_SEMANTIC_PROFILE_VARIANT).strip().lower().replace("-", "_")
    aliases = {
        "baseline": "control",
        "default": "control",
        "current": "control",
        "hostnamefirst": "hostname_first",
        "rolescopefirst": "role_scope_first",
    }
    return aliases.get(variant, variant)


def get_semantic_profile_variant() -> str:
    from os import environ

    return normalize_variant(environ.get(SEMANTIC_PROFILE_VARIANT_ENV))


def summarize_scope(ip_scope: str, element_kind: str, canonical_hostname: str | None, canonical_ip: str | None, role_hint_current: str) -> str:
    if ip_scope == "public" and canonical_hostname:
        if role_hint_current == "destination":
            return f"public destination hostname {canonical_hostname}"
        return f"public hostname {canonical_hostname}"
    if ip_scope == "public" and canonical_ip:
        return f"public node ip {canonical_ip}"
    if ip_scope == "private":
        return "private hop element from network_hop observations"
    return f"{element_kind} element with role {role_hint_current}"


def _base_profile_lines(row: dict[str, Any]) -> list[str]:
    return [
        "Topomemory semantic profile v1",
        f"element_id: {format_value(row.get('element_id'))}",
        f"canonical_label: {format_value(row.get('canonical_label'))}",
        f"element_kind: {format_value(row.get('element_kind'))}",
        f"ip_scope: {format_value(row.get('ip_scope'))}",
        f"canonical_ip: {format_value(row.get('canonical_ip'))}",
        f"canonical_hostname: {format_value(row.get('canonical_hostname'))}",
        f"canonical_asn: {format_value(row.get('canonical_asn'))}",
        f"canonical_org: {format_value(row.get('canonical_org'))}",
        f"confidence_current: {float(row.get('confidence_current') or 0):.3f}",
        f"role_hint_current: {format_value(row.get('role_hint_current'))}",
        f"first_seen_at: {format_value(row.get('first_seen_at'))}",
        f"last_seen_at: {format_value(row.get('last_seen_at'))}",
        f"observed_decision_count: {int(row.get('decision_count') or 0)}",
        f"matched_existing_entity_count: {int(row.get('matched_count') or 0)}",
        f"new_entity_created_count: {int(row.get('new_count') or 0)}",
        f"skipped_decision_count: {int(row.get('skipped_count') or 0)}",
        f"distinct_run_count: {int(row.get('run_count') or 0)}",
        f"observed_source_types: {format_value(row.get('source_types'))}",
        f"observed_ip_scopes: {format_value(row.get('observed_ip_scopes'))}",
        f"observed_service_contexts: {format_value(row.get('service_contexts'))}",
    ]


def _control_profile_lines(row: dict[str, Any]) -> list[str]:
    profile_lines = _base_profile_lines(row)
    profile_lines.append(
        f"audit_summary: {summarize_scope(
            str(row.get('ip_scope') or 'unknown'),
            str(row.get('element_kind') or 'unknown'),
            row.get('canonical_hostname'),
            row.get('canonical_ip'),
            str(row.get('role_hint_current') or 'unknown'),
        )}"
    )
    return profile_lines


def _hostname_first_profile_lines(row: dict[str, Any]) -> list[str]:
    canonical_hostname = format_value(row.get("canonical_hostname"))
    canonical_label = format_value(row.get("canonical_label"))
    canonical_org = format_value(row.get("canonical_org"))
    canonical_ip = format_value(row.get("canonical_ip"))
    role_hint_current = format_value(row.get("role_hint_current"))
    ip_scope = format_value(row.get("ip_scope"))
    element_kind = format_value(row.get("element_kind"))
    profile_lines = [
        "Topomemory semantic profile v1",
        "profile_variant: hostname_first",
        f"element_id: {format_value(row.get('element_id'))}",
        f"canonical_hostname: {canonical_hostname}",
        f"canonical_label: {canonical_label}",
        f"canonical_org: {canonical_org}",
        f"canonical_ip: {canonical_ip}",
        f"element_kind: {element_kind}",
        f"ip_scope: {ip_scope}",
        f"role_hint_current: {role_hint_current}",
        f"canonical_asn: {format_value(row.get('canonical_asn'))}",
        f"confidence_current: {float(row.get('confidence_current') or 0):.3f}",
        f"first_seen_at: {format_value(row.get('first_seen_at'))}",
        f"last_seen_at: {format_value(row.get('last_seen_at'))}",
        f"hostname_anchor: {canonical_hostname} {canonical_label}",
        f"search_focus: hostname label org public private destination node hop route",
        f"search_tokens: {' '.join(split_tokens(canonical_hostname) + split_tokens(canonical_label) + split_tokens(canonical_org))}",
        f"observed_service_contexts: {format_value(row.get('service_contexts'))}",
        f"audit_summary: {summarize_scope(
            str(row.get('ip_scope') or 'unknown'),
            str(row.get('element_kind') or 'unknown'),
            row.get('canonical_hostname'),
            row.get('canonical_ip'),
            str(row.get('role_hint_current') or 'unknown'),
        )}",
    ]
    return profile_lines


def _role_scope_first_profile_lines(row: dict[str, Any]) -> list[str]:
    canonical_hostname = format_value(row.get("canonical_hostname"))
    canonical_label = format_value(row.get("canonical_label"))
    canonical_org = format_value(row.get("canonical_org"))
    canonical_ip = format_value(row.get("canonical_ip"))
    role_hint_current = format_value(row.get("role_hint_current"))
    ip_scope = format_value(row.get("ip_scope"))
    element_kind = format_value(row.get("element_kind"))
    profile_lines = [
        "Topomemory semantic profile v1",
        "profile_variant: role_scope_first",
        f"element_id: {format_value(row.get('element_id'))}",
        f"ip_scope: {ip_scope}",
        f"role_hint_current: {role_hint_current}",
        f"element_kind: {element_kind}",
        f"canonical_label: {canonical_label}",
        f"canonical_hostname: {canonical_hostname}",
        f"canonical_ip: {canonical_ip}",
        f"canonical_org: {canonical_org}",
        f"canonical_asn: {format_value(row.get('canonical_asn'))}",
        f"confidence_current: {float(row.get('confidence_current') or 0):.3f}",
        f"scope_anchor: {ip_scope} {role_hint_current} {element_kind}",
        f"search_focus: public private destination node hop route element scope",
        f"search_tokens: {' '.join(split_tokens(ip_scope) + split_tokens(role_hint_current) + split_tokens(element_kind) + split_tokens(canonical_label))}",
        f"observed_service_contexts: {format_value(row.get('service_contexts'))}",
        f"audit_summary: {summarize_scope(
            str(row.get('ip_scope') or 'unknown'),
            str(row.get('element_kind') or 'unknown'),
            row.get('canonical_hostname'),
            row.get('canonical_ip'),
            str(row.get('role_hint_current') or 'unknown'),
        )}",
    ]
    return profile_lines


def _hybrid_profile_lines(row: dict[str, Any]) -> list[str]:
    canonical_hostname = format_value(row.get("canonical_hostname"))
    canonical_label = format_value(row.get("canonical_label"))
    canonical_org = format_value(row.get("canonical_org"))
    canonical_ip = format_value(row.get("canonical_ip"))
    role_hint_current = format_value(row.get("role_hint_current"))
    ip_scope = format_value(row.get("ip_scope"))
    element_kind = format_value(row.get("element_kind"))
    profile_lines = [
        "Topomemory semantic profile v1",
        "profile_variant: hybrid",
        f"element_id: {format_value(row.get('element_id'))}",
        f"canonical_hostname: {canonical_hostname}",
        f"canonical_label: {canonical_label}",
        f"ip_scope: {ip_scope}",
        f"role_hint_current: {role_hint_current}",
        f"element_kind: {element_kind}",
        f"canonical_ip: {canonical_ip}",
        f"canonical_org: {canonical_org}",
        f"canonical_asn: {format_value(row.get('canonical_asn'))}",
        f"confidence_current: {float(row.get('confidence_current') or 0):.3f}",
        f"hostname_anchor: {canonical_hostname} {canonical_label}",
        f"scope_anchor: {ip_scope} {role_hint_current} {element_kind}",
        f"search_focus: hostname public private destination node hop route element",
        f"search_tokens: {' '.join(split_tokens(canonical_hostname) + split_tokens(canonical_label) + split_tokens(ip_scope) + split_tokens(role_hint_current) + split_tokens(element_kind) + split_tokens(canonical_org))}",
        f"observed_service_contexts: {format_value(row.get('service_contexts'))}",
        f"audit_summary: {summarize_scope(
            str(row.get('ip_scope') or 'unknown'),
            str(row.get('element_kind') or 'unknown'),
            row.get('canonical_hostname'),
            row.get('canonical_ip'),
            str(row.get('role_hint_current') or 'unknown'),
        )}",
    ]
    return profile_lines


def _private_node_first_profile_lines(row: dict[str, Any]) -> list[str]:
    canonical_hostname = format_value(row.get("canonical_hostname"))
    canonical_label = format_value(row.get("canonical_label"))
    canonical_org = format_value(row.get("canonical_org"))
    canonical_ip = format_value(row.get("canonical_ip"))
    role_hint_current = format_value(row.get("role_hint_current"))
    ip_scope = format_value(row.get("ip_scope"))
    element_kind = format_value(row.get("element_kind"))
    private_anchor = "private node" if ip_scope == "private" else "public node"
    profile_lines = [
        "Topomemory semantic profile v1",
        "profile_variant: private_node_first",
        f"element_id: {format_value(row.get('element_id'))}",
        f"ip_scope: {ip_scope}",
        f"role_hint_current: {role_hint_current}",
        f"element_kind: {element_kind}",
        f"canonical_hostname: {canonical_hostname}",
        f"canonical_label: {canonical_label}",
        f"canonical_ip: {canonical_ip}",
        f"canonical_org: {canonical_org}",
        f"canonical_asn: {format_value(row.get('canonical_asn'))}",
        f"confidence_current: {float(row.get('confidence_current') or 0):.3f}",
        f"private_anchor: {private_anchor}",
        f"scope_anchor: {ip_scope} {role_hint_current} {element_kind}",
        f"search_focus: private node private hop route element public destination hostname",
        f"search_tokens: {' '.join(split_tokens(ip_scope) + split_tokens(role_hint_current) + split_tokens(element_kind) + split_tokens(canonical_hostname) + split_tokens(canonical_label))}",
        f"observed_service_contexts: {format_value(row.get('service_contexts'))}",
        f"audit_summary: {summarize_scope(
            str(row.get('ip_scope') or 'unknown'),
            str(row.get('element_kind') or 'unknown'),
            row.get('canonical_hostname'),
            row.get('canonical_ip'),
            str(row.get('role_hint_current') or 'unknown'),
        )}",
    ]
    return profile_lines


def _private_label_tokens(value: str | None) -> str:
    if not value:
        return "none"
    tokens: list[str] = []
    for raw in str(value).replace(".", " ").replace("-", " ").replace("_", " ").replace(":", " ").split():
        cleaned = "".join(ch for ch in raw.lower() if ch.isalnum())
        if cleaned:
            tokens.append(cleaned)
    return " ".join(tokens) if tokens else "none"


def _private_emphasis_profile_lines(row: dict[str, Any]) -> list[str]:
    canonical_hostname = format_value(row.get("canonical_hostname"))
    canonical_label = format_value(row.get("canonical_label"))
    canonical_org = format_value(row.get("canonical_org"))
    canonical_ip = format_value(row.get("canonical_ip"))
    role_hint_current = format_value(row.get("role_hint_current"))
    ip_scope = format_value(row.get("ip_scope"))
    element_kind = format_value(row.get("element_kind"))
    is_private = ip_scope == "private"
    private_anchor = "private node" if is_private else "public node"
    private_focus = "private node private hop internal node internal route element" if is_private else "public node public destination hostname"
    profile_lines = [
        "Topomemory semantic profile v1",
        "profile_variant: hybrid_private_emphasis",
        f"element_id: {format_value(row.get('element_id'))}",
        f"ip_scope: {ip_scope}",
        f"role_hint_current: {role_hint_current}",
        f"element_kind: {element_kind}",
        f"canonical_hostname: {canonical_hostname}",
        f"canonical_label: {canonical_label}",
        f"canonical_ip: {canonical_ip}",
        f"canonical_org: {canonical_org}",
        f"canonical_asn: {format_value(row.get('canonical_asn'))}",
        f"confidence_current: {float(row.get('confidence_current') or 0):.3f}",
        f"private_anchor: {private_anchor}",
        f"private_focus: {private_focus}",
        f"private_focus_repeat: {private_focus} {private_focus}",
        f"private_label_tokens: {_private_label_tokens(row.get('canonical_label'))}",
        f"scope_anchor: {ip_scope} {role_hint_current} {element_kind}",
        f"search_focus: private node private hop route element public destination hostname internal",
        f"search_tokens: {' '.join(split_tokens(ip_scope) + split_tokens(role_hint_current) + split_tokens(element_kind) + split_tokens(canonical_hostname) + split_tokens(canonical_org) + split_tokens(canonical_label))}",
        f"observed_service_contexts: {format_value(row.get('service_contexts'))}",
        f"audit_summary: {summarize_scope(
            str(row.get('ip_scope') or 'unknown'),
            str(row.get('element_kind') or 'unknown'),
            row.get('canonical_hostname'),
            row.get('canonical_ip'),
            str(row.get('role_hint_current') or 'unknown'),
        )}",
    ]
    return profile_lines


def _private_signature_profile_lines(row: dict[str, Any]) -> list[str]:
    canonical_hostname = format_value(row.get("canonical_hostname"))
    canonical_label = format_value(row.get("canonical_label"))
    canonical_org = format_value(row.get("canonical_org"))
    canonical_ip = format_value(row.get("canonical_ip"))
    role_hint_current = format_value(row.get("role_hint_current"))
    ip_scope = format_value(row.get("ip_scope"))
    element_kind = format_value(row.get("element_kind"))
    is_private = ip_scope == "private"
    private_focus = "private node private hop internal node internal route element" if is_private else "public node public destination hostname"
    private_signature = " ".join(
        [
            "private" if is_private else "public",
            str(row.get("element_id") or ""),
            str(row.get("canonical_label") or ""),
            str(row.get("canonical_hostname") or ""),
            str(row.get("role_hint_current") or ""),
            str(row.get("element_kind") or ""),
        ]
    ).strip()
    profile_lines = [
        "Topomemory semantic profile v1",
        "profile_variant: hybrid_private_signature",
        f"element_id: {format_value(row.get('element_id'))}",
        f"ip_scope: {ip_scope}",
        f"role_hint_current: {role_hint_current}",
        f"element_kind: {element_kind}",
        f"canonical_hostname: {canonical_hostname}",
        f"canonical_label: {canonical_label}",
        f"canonical_ip: {canonical_ip}",
        f"canonical_org: {canonical_org}",
        f"canonical_asn: {format_value(row.get('canonical_asn'))}",
        f"confidence_current: {float(row.get('confidence_current') or 0):.3f}",
        f"private_focus: {private_focus}",
        f"private_signature: {private_signature}",
        f"private_label_tokens: {_private_label_tokens(row.get('canonical_label'))}",
        f"scope_anchor: {ip_scope} {role_hint_current} {element_kind}",
        f"search_focus: private node private hop route element public destination hostname internal signature",
        f"search_tokens: {' '.join(split_tokens(ip_scope) + split_tokens(role_hint_current) + split_tokens(element_kind) + split_tokens(canonical_hostname) + split_tokens(canonical_org) + split_tokens(canonical_label) + split_tokens(private_signature))}",
        f"observed_service_contexts: {format_value(row.get('service_contexts'))}",
        f"audit_summary: {summarize_scope(
            str(row.get('ip_scope') or 'unknown'),
            str(row.get('element_kind') or 'unknown'),
            row.get('canonical_hostname'),
            row.get('canonical_ip'),
            str(row.get('role_hint_current') or 'unknown'),
        )}",
    ]
    return profile_lines


def _private_boost_profile_lines(row: dict[str, Any]) -> list[str]:
    canonical_hostname = format_value(row.get("canonical_hostname"))
    canonical_label = format_value(row.get("canonical_label"))
    canonical_org = format_value(row.get("canonical_org"))
    canonical_ip = format_value(row.get("canonical_ip"))
    role_hint_current = format_value(row.get("role_hint_current"))
    ip_scope = format_value(row.get("ip_scope"))
    element_kind = format_value(row.get("element_kind"))
    is_private = ip_scope == "private"
    if not is_private:
        return _hybrid_profile_lines(row)

    private_node_phrase = "private node"
    private_focus = "private node private hop internal node internal route element"
    private_query_anchor = "private node private node private node"
    profile_lines = [
        "Topomemory semantic profile v1",
        "profile_variant: hybrid_private_boost",
        f"element_id: {format_value(row.get('element_id'))}",
        f"private_query_anchor: {private_query_anchor}",
        f"private_focus: {private_focus}",
        f"private_focus_repeat: {private_focus} {private_focus} {private_focus}",
        f"private_scope_anchor: {private_node_phrase} internal hop route element",
        f"private_label_tokens: {_private_label_tokens(row.get('canonical_label'))}",
        f"ip_scope: {ip_scope}",
        f"role_hint_current: {role_hint_current}",
        f"element_kind: {element_kind}",
        f"canonical_hostname: {canonical_hostname}",
        f"canonical_label: {canonical_label}",
        f"canonical_ip: {canonical_ip}",
        f"canonical_org: {canonical_org}",
        f"canonical_asn: {format_value(row.get('canonical_asn'))}",
        f"confidence_current: {float(row.get('confidence_current') or 0):.3f}",
        f"private_signature: {' '.join([private_node_phrase, canonical_label, canonical_hostname, role_hint_current, element_kind]).strip()}",
        f"search_focus: private node private node private node private hop internal node internal route element private destination hostname",
        f"search_tokens: {' '.join(split_tokens(ip_scope) + split_tokens(role_hint_current) + split_tokens(element_kind) + split_tokens(canonical_hostname) + split_tokens(canonical_org) + split_tokens(canonical_label))}",
        f"observed_service_contexts: {format_value(row.get('service_contexts'))}",
        f"audit_summary: {summarize_scope(
            str(row.get('ip_scope') or 'unknown'),
            str(row.get('element_kind') or 'unknown'),
            row.get('canonical_hostname'),
            row.get('canonical_ip'),
            str(row.get('role_hint_current') or 'unknown'),
        )}",
    ]
    return profile_lines


def _private_node_focus_profile_lines(row: dict[str, Any]) -> list[str]:
    canonical_hostname = format_value(row.get("canonical_hostname"))
    canonical_label = format_value(row.get("canonical_label"))
    canonical_org = format_value(row.get("canonical_org"))
    canonical_ip = format_value(row.get("canonical_ip"))
    role_hint_current = format_value(row.get("role_hint_current"))
    ip_scope = format_value(row.get("ip_scope"))
    element_kind = format_value(row.get("element_kind"))
    is_private = ip_scope == "private"
    if not is_private:
        return _hybrid_profile_lines(row)

    private_focus = "private node private hop internal node internal route element"
    private_anchor = "private node private node private hop internal route element"
    profile_lines = [
        "Topomemory semantic profile v1",
        "profile_variant: hybrid_private_node_focus",
        f"element_id: {format_value(row.get('element_id'))}",
        f"private_anchor: {private_anchor}",
        f"private_focus: {private_focus}",
        f"private_focus_repeat: {private_focus} {private_focus}",
        f"private_scope_anchor: private node internal hop route element",
        f"private_label_tokens: {_private_label_tokens(row.get('canonical_label'))}",
        f"ip_scope: {ip_scope}",
        f"role_hint_current: {role_hint_current}",
        f"element_kind: {element_kind}",
        f"canonical_hostname: {canonical_hostname}",
        f"canonical_label: {canonical_label}",
        f"canonical_ip: {canonical_ip}",
        f"canonical_org: {canonical_org}",
        f"canonical_asn: {format_value(row.get('canonical_asn'))}",
        f"confidence_current: {float(row.get('confidence_current') or 0):.3f}",
        f"private_signature: {' '.join([canonical_label, role_hint_current, element_kind, canonical_org]).strip()}",
        f"search_focus: private node private hop internal node internal route element private private private node node hop route element",
        f"search_tokens: {' '.join(split_tokens(ip_scope) + split_tokens(role_hint_current) + split_tokens(element_kind) + split_tokens(canonical_hostname) + split_tokens(canonical_org) + split_tokens(canonical_label))}",
        f"observed_service_contexts: {format_value(row.get('service_contexts'))}",
        f"audit_summary: {summarize_scope(
            str(row.get('ip_scope') or 'unknown'),
            str(row.get('element_kind') or 'unknown'),
            row.get('canonical_hostname'),
            row.get('canonical_ip'),
            str(row.get('role_hint_current') or 'unknown'),
        )}",
    ]
    return profile_lines


def _private_page8_focus_profile_lines(row: dict[str, Any]) -> list[str]:
    canonical_label = format_value(row.get("canonical_label"))
    is_private = str(row.get("ip_scope") or "") == "private"
    is_page8 = is_private and ":8:" in str(row.get("canonical_label") or "")
    if not is_page8:
        return _hybrid_profile_lines(row)

    canonical_hostname = format_value(row.get("canonical_hostname"))
    canonical_org = format_value(row.get("canonical_org"))
    canonical_ip = format_value(row.get("canonical_ip"))
    role_hint_current = format_value(row.get("role_hint_current"))
    element_kind = format_value(row.get("element_kind"))
    private_focus = "private node private hop internal node internal route element"
    private_anchor = "private node private node private node private hop internal route element"
    profile_lines = [
        "Topomemory semantic profile v1",
        "profile_variant: hybrid_private_page8_focus",
        f"element_id: {format_value(row.get('element_id'))}",
        f"private_anchor: {private_anchor}",
        f"private_focus: {private_focus}",
        f"private_focus_repeat: {private_focus} {private_focus} {private_focus}",
        f"private_label_tokens: {_private_label_tokens(canonical_label)}",
        f"ip_scope: private",
        f"role_hint_current: {role_hint_current}",
        f"element_kind: {element_kind}",
        f"canonical_hostname: {canonical_hostname}",
        f"canonical_label: {canonical_label}",
        f"canonical_ip: {canonical_ip}",
        f"canonical_org: {canonical_org}",
        f"canonical_asn: {format_value(row.get('canonical_asn'))}",
        f"confidence_current: {float(row.get('confidence_current') or 0):.3f}",
        f"private_signature: {' '.join([canonical_label, role_hint_current, element_kind]).strip()}",
        f"search_focus: private node private hop internal node internal route element private private node node hop route element",
        f"search_tokens: {' '.join(split_tokens(canonical_label) + split_tokens(role_hint_current) + split_tokens(element_kind) + split_tokens(canonical_org))}",
        f"observed_service_contexts: {format_value(row.get('service_contexts'))}",
        f"audit_summary: {summarize_scope(
            str(row.get('ip_scope') or 'unknown'),
            str(row.get('element_kind') or 'unknown'),
            row.get('canonical_hostname'),
            row.get('canonical_ip'),
            str(row.get('role_hint_current') or 'unknown'),
        )}",
    ]
    return profile_lines


def build_semantic_profile_text(row: dict[str, Any], *, variant: str | None = None) -> str:
    active_variant = normalize_variant(variant or get_semantic_profile_variant())
    if active_variant == "hostname_first":
        lines = _hostname_first_profile_lines(row)
    elif active_variant == "role_scope_first":
        lines = _role_scope_first_profile_lines(row)
    elif active_variant == "hybrid":
        lines = _hybrid_profile_lines(row)
    elif active_variant == "private_node_first":
        lines = _private_node_first_profile_lines(row)
    elif active_variant == "hybrid_private_emphasis":
        lines = _private_emphasis_profile_lines(row)
    elif active_variant == "hybrid_private_signature":
        lines = _private_signature_profile_lines(row)
    elif active_variant == "hybrid_private_boost":
        lines = _private_boost_profile_lines(row)
    elif active_variant == "hybrid_private_node_focus":
        lines = _private_node_focus_profile_lines(row)
    elif active_variant == "hybrid_private_page8_focus":
        lines = _private_page8_focus_profile_lines(row)
    else:
        lines = _control_profile_lines(row)
    return "\n".join(lines) + "\n"
