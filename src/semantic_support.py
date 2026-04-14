#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import math
import re
from datetime import datetime
from typing import Any, Sequence

EMBEDDING_DIMENSIONS = 128
EMBEDDING_MODEL = "topomemory-hash-embedding-v1"
SEMANTIC_PROFILE_VERSION = "semantic-profile-v1"

TOKEN_RE = re.compile(r"[a-z0-9]+")


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


def tokenize_text(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def token_features(text: str) -> list[str]:
    tokens = tokenize_text(text)
    features: list[str] = []
    features.extend(tokens)
    features.extend(f"{left}_{right}" for left, right in zip(tokens, tokens[1:]))
    features.extend(f"{left}_{middle}_{right}" for left, middle, right in zip(tokens, tokens[1:], tokens[2:]))
    return features


def vector_literal(values: Sequence[float]) -> str:
    return "[" + ",".join(f"{value:.6f}" for value in values) + "]"


def embed_text(text: str, dimensions: int = EMBEDDING_DIMENSIONS) -> list[float]:
    vector = [0.0] * dimensions
    features = token_features(text)
    if not features:
        return vector

    for feature in features:
        digest = hashlib.sha256(feature.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] & 1 else -1.0
        weight = 1.0
        if "_" in feature:
            weight = 0.75
        if feature.count("_") >= 2:
            weight = 0.5
        vector[index] += sign * weight

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]
