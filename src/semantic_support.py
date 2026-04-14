#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from typing import Any

SEMANTIC_PROFILE_VERSION = "semantic-profile-v1"


def format_value(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    text = str(value).strip()
    return text if text else "none"


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


def build_semantic_profile_text(row: dict[str, Any]) -> str:
    profile_lines = [
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
        f"audit_summary: {summarize_scope(
            str(row.get('ip_scope') or 'unknown'),
            str(row.get('element_kind') or 'unknown'),
            row.get('canonical_hostname'),
            row.get('canonical_ip'),
            str(row.get('role_hint_current') or 'unknown'),
        )}",
    ]
    return "\n".join(profile_lines) + "\n"
