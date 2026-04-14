#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import psycopg
from psycopg.types.json import Jsonb


class ConsolidationError(Exception):
    pass


IP_CANDIDATE_RE = re.compile(
    r"((?:\d{1,3}\.){3}\d{1,3})|([0-9A-Fa-f]{0,4}(?::[0-9A-Fa-f]{0,4}){2,})"
)
HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)(?:\.(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?))*$"
)
WEAK_HOSTNAME_EXACTS = {
    "localhost",
    "localhost.localdomain",
    "localdomain",
    "local",
    "unknown",
}


@dataclass(frozen=True)
class ObservedElement:
    observed_element_id: str
    bundle_id: str
    run_id: str
    element_index: int
    observed_ip: str | None
    observed_hostname: str | None
    observed_ptr: str | None
    hop_index: int | None
    service_context: str | None
    observed_asn: str | None
    observed_org: str | None
    source_type: str
    observed_at: datetime
    raw_json: dict[str, Any]
    target_type: str
    target_value: str
    service_hint: str
    scenario: str


@dataclass(frozen=True)
class ObservedRelation:
    run_id: str
    relation_index: int
    from_element_index: int
    to_element_index: int
    relation_type: str
    relation_order: int
    confidence_hint: float | None


def parse_timestamp(value: str, field_name: str) -> datetime:
    candidate = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ConsolidationError(f"timestamp inválido em {field_name}: {value}") from exc
    if parsed.tzinfo is None:
        raise ConsolidationError(f"timestamp {field_name} precisa ter timezone explícito")
    return parsed


def db_connect(database_url: str) -> psycopg.Connection[Any]:
    return psycopg.connect(database_url)


def require_args(args: argparse.Namespace) -> str:
    modes = [bool(args.run_id), bool(args.bundle_id), bool(args.all_unconsolidated)]
    if sum(modes) != 1:
        raise ConsolidationError("é obrigatório informar exatamente um entre --run-id, --bundle-id ou --all-unconsolidated")

    if args.run_id:
        return "run_id"
    if args.bundle_id:
        return "bundle_id"
    return "all_unconsolidated"


def load_observed_elements(conn: psycopg.Connection[Any], args: argparse.Namespace) -> list[ObservedElement]:
    where_clause = ""
    params: tuple[Any, ...] = ()

    if args.run_id:
        where_clause = "oe.run_id = %s"
        params = (args.run_id,)
    elif args.bundle_id:
        where_clause = "oe.bundle_id = %s"
        params = (args.bundle_id,)
    else:
        where_clause = "NOT EXISTS (SELECT 1 FROM topomemory.identity_decision id WHERE id.observed_element_id = oe.observed_element_id)"

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT
              oe.observed_element_id,
              oe.bundle_id,
              oe.run_id,
              oe.element_index,
              oe.observed_ip,
              oe.observed_hostname,
              oe.observed_ptr,
              oe.hop_index,
              oe.service_context,
              oe.observed_asn,
              oe.observed_org,
              oe.source_type,
              oe.observed_at,
              oe.raw_json,
              r.target_type,
              r.target_value,
              r.service_hint,
              r.scenario
            FROM topomemory.observed_element oe
            JOIN topomemory.run r ON r.run_id = oe.run_id
            WHERE {where_clause}
            ORDER BY oe.run_id, oe.element_index
            """,
            params,
        )
        rows = cur.fetchall()

    result: list[ObservedElement] = []
    for row in rows:
        (
            observed_element_id,
            bundle_id,
            run_id,
            element_index,
            observed_ip,
            observed_hostname,
            observed_ptr,
            hop_index,
            service_context,
            observed_asn,
            observed_org,
            source_type,
            observed_at,
            raw_json,
            target_type,
            target_value,
            service_hint,
            scenario,
        ) = row
        result.append(
            ObservedElement(
                observed_element_id=observed_element_id,
                bundle_id=bundle_id,
                run_id=run_id,
                element_index=element_index,
                observed_ip=observed_ip,
                observed_hostname=observed_hostname,
                observed_ptr=observed_ptr,
                hop_index=hop_index,
                service_context=service_context,
                observed_asn=observed_asn,
                observed_org=observed_org,
                source_type=source_type,
                observed_at=observed_at,
                raw_json=raw_json,
                target_type=target_type,
                target_value=target_value,
                service_hint=service_hint,
                scenario=scenario,
            )
        )

    return result


def load_observed_relations(conn: psycopg.Connection[Any], args: argparse.Namespace) -> list[ObservedRelation]:
    where_clause = ""
    params: tuple[Any, ...] = ()

    if args.run_id:
        where_clause = "orl.run_id = %s"
        params = (args.run_id,)
    elif args.bundle_id:
        where_clause = "orl.bundle_id = %s"
        params = (args.bundle_id,)
    else:
        where_clause = "NOT EXISTS (SELECT 1 FROM topomemory.identity_decision id WHERE id.run_id = orl.run_id)"

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT
              orl.run_id,
              orl.relation_index,
              orl.from_element_index,
              orl.to_element_index,
              orl.relation_type,
              orl.relation_order,
              orl.confidence_hint
            FROM topomemory.observed_relation orl
            WHERE {where_clause}
            ORDER BY orl.run_id, orl.relation_index
            """,
            params,
        )
        rows = cur.fetchall()

    return [
        ObservedRelation(
            run_id=row[0],
            relation_index=row[1],
            from_element_index=row[2],
            to_element_index=row[3],
            relation_type=row[4],
            relation_order=row[5],
            confidence_hint=row[6],
        )
        for row in rows
    ]


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def normalize_hostname(value: str | None) -> str | None:
    candidate = normalize_text(value)
    if candidate is None:
        return None
    candidate = candidate.lower().rstrip(".")
    if not candidate:
        return None
    if " " in candidate or "/" in candidate or "\\" in candidate:
        return None
    return candidate


def is_strong_hostname(value: str | None) -> bool:
    candidate = normalize_hostname(value)
    if candidate is None:
        return False
    if candidate in WEAK_HOSTNAME_EXACTS:
        return False
    if candidate.count(".") < 1:
        return False
    if len(candidate) > 253:
        return False
    return bool(HOSTNAME_RE.fullmatch(candidate))


def preferred_hostname(element: ObservedElement) -> tuple[str | None, str | None]:
    normalized_hostname = normalize_hostname(element.observed_hostname)
    normalized_ptr = normalize_hostname(element.observed_ptr)

    hostname_strong = normalized_hostname if is_strong_hostname(normalized_hostname) else None
    ptr_strong = normalized_ptr if is_strong_hostname(normalized_ptr) else None

    if hostname_strong and ptr_strong and hostname_strong != ptr_strong:
        return None, "hostname_ptr_conflict"
    if hostname_strong:
        return hostname_strong, None
    if ptr_strong:
        return ptr_strong, None
    if normalized_hostname or normalized_ptr:
        return None, "hostname_weak"
    return None, None


def normalized_service_context(element: ObservedElement) -> str | None:
    candidate = normalize_text(element.service_context)
    if candidate is not None:
        return candidate
    return normalize_text(element.service_hint)


def extract_ip_value(value: str | None) -> str | None:
    candidate = normalize_text(value)
    if candidate is None:
        return None
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        match = IP_CANDIDATE_RE.search(candidate)
        if match is None:
            return None
        for group in match.groups():
            if not group:
                continue
            try:
                return str(ipaddress.ip_address(group))
            except ValueError:
                continue
    return None


def canonicalize_ip(value: str | None) -> str:
    candidate = extract_ip_value(value)
    if candidate is None:
        raise ValueError(f"valor sem IP canônico: {value!r}")
    return candidate


def is_public_ip(value: str | None) -> bool:
    candidate = extract_ip_value(value)
    if not candidate:
        return False
    try:
        ip = ipaddress.ip_address(candidate)
    except ValueError:
        return False
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
        or ip.is_global is False
    )


def classify_scope(element: ObservedElement) -> str:
    candidate_ip = extract_ip_value(element.observed_ip)
    if candidate_ip:
        ip = ipaddress.ip_address(candidate_ip)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
            or ip.is_global is False
        ):
            return "private"
        return "public"

    if normalize_text(element.observed_hostname) or element.source_type == "target":
        return "public"

    return "unknown"


def stable_id(prefix: str, value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return f"{prefix}-{cleaned or 'item'}"


def element_kind_for(element: ObservedElement, scope: str) -> str:
    if scope != "public":
        return "unknown"
    if element.source_type == "target":
        return "destination"
    return "public_node"


def role_hint_for(element: ObservedElement) -> str:
    if element.source_type == "target":
        return "destination"
    return "unknown"


def confidence_for(decision_type: str) -> float:
    if decision_type == "matched_existing_entity":
        return 0.980
    if decision_type == "new_entity_created":
        return 0.970
    return 0.000


def numeric3(value: Any) -> str:
    return f"{value:.3f}"


def public_identity_key_for_element(element: ObservedElement) -> str:
    candidate_ip = extract_ip_value(element.observed_ip)
    if candidate_ip and is_public_ip(candidate_ip):
        return f"ip:{candidate_ip}"

    hostname, _ = preferred_hostname(element)
    if hostname is not None:
        return f"host:{hostname}"

    return f"idx:{element.run_id}:{element.element_index}"


def element_identity_key(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest


def private_identity_key_for_element(
    element: ObservedElement,
    previous_neighbor_key: str | None,
    next_neighbor_key: str | None,
) -> str | None:
    candidate_ip = extract_ip_value(element.observed_ip)
    if candidate_ip is None:
        return None
    try:
        ip = ipaddress.ip_address(candidate_ip)
    except ValueError:
        return None
    if not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
        or ip.is_global is False
    ):
        return None

    service_context = normalized_service_context(element)
    hop_index = element.hop_index
    if service_context is None or hop_index is None:
        return None
    if previous_neighbor_key is None and next_neighbor_key is None:
        return None

    parts = [
        candidate_ip,
        str(hop_index),
        previous_neighbor_key or "missing-prev",
        next_neighbor_key or "missing-next",
        service_context,
    ]
    return element_identity_key("|".join(parts))


def build_bundle_index(elements: list[ObservedElement]) -> dict[tuple[str, int], ObservedElement]:
    return {(element.run_id, element.element_index): element for element in elements}


def build_relation_neighbors(relations: list[ObservedRelation]) -> dict[str, dict[int, dict[str, list[int]]]]:
    result: dict[str, dict[int, dict[str, list[int]]]] = {}
    for relation in relations:
        run_map = result.setdefault(relation.run_id, {})
        from_bucket = run_map.setdefault(relation.from_element_index, {"prev": [], "next": []})
        to_bucket = run_map.setdefault(relation.to_element_index, {"prev": [], "next": []})
        if relation.relation_type == "precedes":
            from_bucket["next"].append(relation.to_element_index)
            to_bucket["prev"].append(relation.from_element_index)
    return result


def select_single_candidate(candidates: list[int]) -> int | None | str:
    unique_candidates = sorted(set(candidates))
    if not unique_candidates:
        return None
    if len(unique_candidates) > 1:
        return "conflict"
    return unique_candidates[0]


def resolve_neighbor_key(
    *,
    current: ObservedElement,
    direction: str,
    bundle_index: dict[tuple[str, int], ObservedElement],
    relation_neighbors: dict[str, dict[int, dict[str, list[int]]]],
) -> str | None | str:
    relation_bucket = relation_neighbors.get(current.run_id, {}).get(current.element_index, {})
    candidate_indexes = relation_bucket.get(direction, [])
    chosen_index = select_single_candidate(candidate_indexes)
    if chosen_index == "conflict":
        return "conflict"
    if isinstance(chosen_index, int):
        neighbor = bundle_index.get((current.run_id, chosen_index))
        if neighbor is not None:
            return public_identity_key_for_element(neighbor)

    fallback_index = current.element_index - 1 if direction == "prev" else current.element_index + 1
    fallback = bundle_index.get((current.run_id, fallback_index))
    if fallback is None:
        return None
    return public_identity_key_for_element(fallback)


def private_canonical_label(element: ObservedElement, private_key: str) -> str:
    hop = element.hop_index if element.hop_index is not None else "na"
    return f"private:{element.service_context or element.service_hint}:{hop}:{private_key[:12]}"


def load_network_element_by_ip(conn: psycopg.Connection[Any], canonical_ip: str) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              element_id,
              canonical_label,
              element_kind,
              ip_scope,
              canonical_ip,
              canonical_hostname,
              canonical_asn,
              canonical_org,
              confidence_current,
              role_hint_current,
              first_seen_at,
              last_seen_at,
              is_active
            FROM topomemory.network_element
            WHERE canonical_ip = %s
            """,
            (canonical_ip,),
        )
        row = cur.fetchone()

    if row is None:
        return None

    return {
        "element_id": row[0],
        "canonical_label": row[1],
        "element_kind": row[2],
        "ip_scope": row[3],
        "canonical_ip": row[4],
        "canonical_hostname": row[5],
        "canonical_asn": row[6],
        "canonical_org": row[7],
        "confidence_current": row[8],
        "role_hint_current": row[9],
        "first_seen_at": row[10],
        "last_seen_at": row[11],
        "is_active": row[12],
    }


def load_network_element_by_element_id(conn: psycopg.Connection[Any], element_id: str) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              element_id,
              canonical_label,
              element_kind,
              ip_scope,
              canonical_ip,
              canonical_hostname,
              canonical_asn,
              canonical_org,
              confidence_current,
              role_hint_current,
              first_seen_at,
              last_seen_at,
              is_active
            FROM topomemory.network_element
            WHERE element_id = %s
            """,
            (element_id,),
        )
        row = cur.fetchone()

    if row is None:
        return None

    return {
        "element_id": row[0],
        "canonical_label": row[1],
        "element_kind": row[2],
        "ip_scope": row[3],
        "canonical_ip": row[4],
        "canonical_hostname": row[5],
        "canonical_asn": row[6],
        "canonical_org": row[7],
        "confidence_current": row[8],
        "role_hint_current": row[9],
        "first_seen_at": row[10],
        "last_seen_at": row[11],
        "is_active": row[12],
    }


def load_network_element_by_hostname(conn: psycopg.Connection[Any], canonical_hostname: str) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              element_id,
              canonical_label,
              element_kind,
              ip_scope,
              canonical_ip,
              canonical_hostname,
              canonical_asn,
              canonical_org,
              confidence_current,
              role_hint_current,
              first_seen_at,
              last_seen_at,
              is_active
            FROM topomemory.network_element
            WHERE canonical_hostname = %s
              AND canonical_ip IS NULL
            ORDER BY first_seen_at ASC, element_id ASC
            LIMIT 1
            """,
            (canonical_hostname,),
        )
        row = cur.fetchone()

    if row is None:
        return None

    return {
        "element_id": row[0],
        "canonical_label": row[1],
        "element_kind": row[2],
        "ip_scope": row[3],
        "canonical_ip": row[4],
        "canonical_hostname": row[5],
        "canonical_asn": row[6],
        "canonical_org": row[7],
        "confidence_current": row[8],
        "role_hint_current": row[9],
        "first_seen_at": row[10],
        "last_seen_at": row[11],
        "is_active": row[12],
    }


def upsert_network_element(
    conn: psycopg.Connection[Any],
    *,
    element_id: str,
    canonical_label: str,
    element_kind: str,
    ip_scope: str,
    canonical_ip: str | None,
    canonical_hostname: str | None,
    canonical_asn: str | None,
    canonical_org: str | None,
    confidence_current: float,
    role_hint_current: str,
    first_seen_at: datetime,
    last_seen_at: datetime,
) -> None:
    existing = None
    if canonical_ip is not None:
        existing = load_network_element_by_ip(conn, canonical_ip)
    elif canonical_hostname is not None:
        existing = load_network_element_by_hostname(conn, canonical_hostname)
    else:
        existing = load_network_element_by_element_id(conn, element_id)

    desired = {
        "element_id": element_id,
        "canonical_label": canonical_label,
        "element_kind": element_kind,
        "ip_scope": ip_scope,
        "canonical_ip": canonical_ip,
        "canonical_hostname": canonical_hostname,
        "canonical_asn": canonical_asn,
        "canonical_org": canonical_org,
        "confidence_current": confidence_current,
        "role_hint_current": role_hint_current,
        "first_seen_at": first_seen_at,
        "last_seen_at": last_seen_at,
    }

    if existing is not None:
        existing_fingerprint = {
            "element_id": existing["element_id"],
            "canonical_label": existing["canonical_label"],
            "element_kind": existing["element_kind"],
            "ip_scope": existing["ip_scope"],
            "canonical_ip": existing["canonical_ip"],
            "canonical_hostname": existing["canonical_hostname"],
            "canonical_asn": existing["canonical_asn"],
            "canonical_org": existing["canonical_org"],
            "confidence_current": numeric3(existing["confidence_current"]),
            "role_hint_current": existing["role_hint_current"],
            "first_seen_at": existing["first_seen_at"],
            "last_seen_at": existing["last_seen_at"],
        }
        desired_fingerprint = dict(desired)
        desired_fingerprint["confidence_current"] = numeric3(desired_fingerprint["confidence_current"])
        if existing_fingerprint == desired_fingerprint:
            return

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO topomemory.network_element (
              element_id,
              canonical_label,
              element_kind,
              ip_scope,
              canonical_ip,
              canonical_hostname,
              canonical_asn,
              canonical_org,
              confidence_current,
              role_hint_current,
              first_seen_at,
              last_seen_at
            )
            VALUES (
              %(element_id)s,
              %(canonical_label)s,
              %(element_kind)s,
              %(ip_scope)s,
              %(canonical_ip)s,
              %(canonical_hostname)s,
              %(canonical_asn)s,
              %(canonical_org)s,
              %(confidence_current)s,
              %(role_hint_current)s,
              %(first_seen_at)s,
              %(last_seen_at)s
            )
            ON CONFLICT (element_id) DO UPDATE SET
              canonical_label = EXCLUDED.canonical_label,
              element_kind = EXCLUDED.element_kind,
              ip_scope = EXCLUDED.ip_scope,
              canonical_ip = EXCLUDED.canonical_ip,
              canonical_hostname = CASE
                WHEN topomemory.network_element.canonical_hostname IS NULL THEN EXCLUDED.canonical_hostname
                ELSE topomemory.network_element.canonical_hostname
              END,
              canonical_asn = CASE
                WHEN topomemory.network_element.canonical_asn IS NULL THEN EXCLUDED.canonical_asn
                ELSE topomemory.network_element.canonical_asn
              END,
              canonical_org = CASE
                WHEN topomemory.network_element.canonical_org IS NULL THEN EXCLUDED.canonical_org
                ELSE topomemory.network_element.canonical_org
              END,
              confidence_current = GREATEST(topomemory.network_element.confidence_current, EXCLUDED.confidence_current),
              role_hint_current = CASE
                WHEN topomemory.network_element.role_hint_current = 'unknown' THEN EXCLUDED.role_hint_current
                ELSE topomemory.network_element.role_hint_current
              END,
              first_seen_at = LEAST(topomemory.network_element.first_seen_at, EXCLUDED.first_seen_at),
              last_seen_at = GREATEST(topomemory.network_element.last_seen_at, EXCLUDED.last_seen_at),
              is_active = TRUE
            """,
            desired,
        )


def load_decision_by_observed_element_id(
    conn: psycopg.Connection[Any], observed_element_id: str
) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              identity_decision_id,
              observed_element_id,
              run_id,
              bundle_id,
              decision_type,
              matched_element_id,
              new_element_id,
              confidence,
              reasoning_summary,
              evidence_json,
              decided_at
            FROM topomemory.identity_decision
            WHERE observed_element_id = %s
            """,
            (observed_element_id,),
        )
        row = cur.fetchone()

    if row is None:
        return None

    return {
        "identity_decision_id": row[0],
        "observed_element_id": row[1],
        "run_id": row[2],
        "bundle_id": row[3],
        "decision_type": row[4],
        "matched_element_id": row[5],
        "new_element_id": row[6],
        "confidence": row[7],
        "reasoning_summary": row[8],
        "evidence_json": row[9],
        "decided_at": row[10],
    }


def upsert_decision(conn: psycopg.Connection[Any], payload: dict[str, Any]) -> None:
    existing = load_decision_by_observed_element_id(conn, payload["observed_element_id"])
    updatable_legacy_types = {
        "skipped_private_scope",
        "skipped_no_public_ip",
        "skipped_hostname_weak",
        "skipped_hostname_conflict",
    }
    if existing is not None:
        if existing["decision_type"] not in updatable_legacy_types:
            return
        if (
            existing["decision_type"] == payload["decision_type"]
            and existing["matched_element_id"] == payload["matched_element_id"]
            and existing["new_element_id"] == payload["new_element_id"]
            and numeric3(existing["confidence"]) == numeric3(payload["confidence"])
            and existing["reasoning_summary"] == payload["reasoning_summary"]
            and existing["evidence_json"] == payload["evidence_json"]
            and existing["decided_at"] == payload["decided_at"]
        ):
            return

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO topomemory.identity_decision (
              identity_decision_id,
              observed_element_id,
              run_id,
              bundle_id,
              decision_type,
              matched_element_id,
              new_element_id,
              confidence,
              reasoning_summary,
              evidence_json,
              decided_at
            )
            VALUES (
              %(identity_decision_id)s,
              %(observed_element_id)s,
              %(run_id)s,
              %(bundle_id)s,
              %(decision_type)s,
              %(matched_element_id)s,
              %(new_element_id)s,
              %(confidence)s,
              %(reasoning_summary)s,
              %(evidence_json)s,
              %(decided_at)s
            )
            ON CONFLICT (observed_element_id) DO UPDATE SET
              run_id = EXCLUDED.run_id,
              bundle_id = EXCLUDED.bundle_id,
              decision_type = EXCLUDED.decision_type,
              matched_element_id = EXCLUDED.matched_element_id,
              new_element_id = EXCLUDED.new_element_id,
              confidence = EXCLUDED.confidence,
              reasoning_summary = EXCLUDED.reasoning_summary,
              evidence_json = EXCLUDED.evidence_json,
              decided_at = EXCLUDED.decided_at
            """,
            {
                **payload,
                "evidence_json": Jsonb(payload["evidence_json"]),
            },
        )


def handle_private_observation(
    conn: psycopg.Connection[Any],
    *,
    element: ObservedElement,
    decided_at: datetime,
    bundle_index: dict[tuple[str, int], ObservedElement],
    relation_neighbors: dict[str, dict[int, dict[str, list[int]]]],
    counters: dict[str, int],
) -> None:
    normalized_hostname = normalize_text(element.observed_hostname)
    normalized_ptr = normalize_text(element.observed_ptr)
    service_context = normalized_service_context(element)

    previous_neighbor_key = resolve_neighbor_key(
        current=element,
        direction="prev",
        bundle_index=bundle_index,
        relation_neighbors=relation_neighbors,
    )
    next_neighbor_key = resolve_neighbor_key(
        current=element,
        direction="next",
        bundle_index=bundle_index,
        relation_neighbors=relation_neighbors,
    )

    if previous_neighbor_key == "conflict" or next_neighbor_key == "conflict":
        counters["private_skipped_conflict"] += 1
        decision_type = "skipped_private_conflict"
        reasoning_summary = "vizinhança privada ambígua no bundle; a consolidação foi adiada para evitar colisão entre contextos."
        decision_payload = {
            "identity_decision_id": f"iddec-{element.observed_element_id}",
            "observed_element_id": element.observed_element_id,
            "run_id": element.run_id,
            "bundle_id": element.bundle_id,
            "decision_type": decision_type,
            "matched_element_id": None,
            "new_element_id": None,
            "confidence": confidence_for(decision_type),
            "reasoning_summary": reasoning_summary,
            "evidence_json": {
                "observed_ip": element.observed_ip,
                "observed_hostname": normalized_hostname,
                "observed_ptr": normalized_ptr,
                "service_context": service_context,
                "hop_index": element.hop_index,
                "previous_neighbor_key": None if previous_neighbor_key == "conflict" else previous_neighbor_key,
                "next_neighbor_key": None if next_neighbor_key == "conflict" else next_neighbor_key,
                "source_type": element.source_type,
                "scope": "private",
                "rule": "private_neighbor_conflict",
            },
            "decided_at": decided_at,
        }
        upsert_decision(conn, decision_payload)
        return

    private_key = private_identity_key_for_element(
        element,
        previous_neighbor_key=previous_neighbor_key if isinstance(previous_neighbor_key, str) else None,
        next_neighbor_key=next_neighbor_key if isinstance(next_neighbor_key, str) else None,
    )
    if private_key is None:
        counters["private_skipped_insufficient_context"] += 1
        decision_type = "skipped_private_insufficient_context"
        reasoning_summary = "observação privada sem contexto local suficiente para uma assinatura determinística conservadora."
        decision_payload = {
            "identity_decision_id": f"iddec-{element.observed_element_id}",
            "observed_element_id": element.observed_element_id,
            "run_id": element.run_id,
            "bundle_id": element.bundle_id,
            "decision_type": decision_type,
            "matched_element_id": None,
            "new_element_id": None,
            "confidence": confidence_for(decision_type),
            "reasoning_summary": reasoning_summary,
            "evidence_json": {
                "observed_ip": element.observed_ip,
                "observed_hostname": normalized_hostname,
                "observed_ptr": normalized_ptr,
                "service_context": service_context,
                "hop_index": element.hop_index,
                "previous_neighbor_key": previous_neighbor_key,
                "next_neighbor_key": next_neighbor_key,
                "source_type": element.source_type,
                "scope": "private",
                "rule": "private_context_insufficient",
            },
            "decided_at": decided_at,
        }
        upsert_decision(conn, decision_payload)
        return

    element_id = f"network-element-private-{private_key}"
    existing = load_network_element_by_element_id(conn, element_id)
    canonical_label = private_canonical_label(element, private_key)
    element_kind = element_kind_for(element, "private")
    role_hint_current = role_hint_for(element)
    confidence = confidence_for("matched_existing_entity" if existing else "new_entity_created")

    if existing:
        counters["private_matched"] += 1
        counters["private_consolidated"] += 1
        decision_type = "matched_existing_entity"
        reasoning_summary = "observação privada combinou com assinatura local determinística já consolidada; identidade reforçada sem merge semântico."
        matched_element_id = existing["element_id"]
        new_element_id = None
        first_seen_at = existing["first_seen_at"]
    else:
        counters["private_new"] += 1
        counters["private_consolidated"] += 1
        decision_type = "new_entity_created"
        reasoning_summary = "observação privada recebeu assinatura local determinística suficiente para criar identidade canônica restrita ao contexto."
        matched_element_id = None
        new_element_id = element_id
        first_seen_at = element.observed_at

    upsert_network_element(
        conn,
        element_id=element_id,
        canonical_label=canonical_label,
        element_kind=element_kind,
        ip_scope="private",
        canonical_ip=None,
        canonical_hostname=None,
        canonical_asn=None,
        canonical_org=None,
        confidence_current=confidence,
        role_hint_current=role_hint_current,
        first_seen_at=first_seen_at,
        last_seen_at=element.observed_at,
    )

    decision_payload = {
        "identity_decision_id": f"iddec-{element.observed_element_id}",
        "observed_element_id": element.observed_element_id,
        "run_id": element.run_id,
        "bundle_id": element.bundle_id,
        "decision_type": decision_type,
        "matched_element_id": matched_element_id,
        "new_element_id": new_element_id,
        "confidence": confidence,
        "reasoning_summary": reasoning_summary,
        "evidence_json": {
            "observed_ip": element.observed_ip,
            "private_identity_key": private_key,
            "observed_hostname": normalized_hostname,
            "observed_ptr": normalized_ptr,
            "service_context": service_context,
            "hop_index": element.hop_index,
            "previous_neighbor_key": previous_neighbor_key,
            "next_neighbor_key": next_neighbor_key,
            "source_type": element.source_type,
            "scope": "private",
            "rule": "private_neighbor_position_signature",
            "matched_existing": existing is not None,
        },
        "decided_at": decided_at,
    }
    upsert_decision(conn, decision_payload)


def consolidate(
    conn: psycopg.Connection[Any],
    elements: list[ObservedElement],
    relations: list[ObservedRelation],
) -> dict[str, int]:
    counters = {
        "observed_elements": 0,
        "public_ip_consolidated": 0,
        "public_ip_matched": 0,
        "public_ip_new": 0,
        "hostname_consolidated": 0,
        "hostname_matched": 0,
        "hostname_new": 0,
        "hostname_skipped_weak": 0,
        "hostname_skipped_conflict": 0,
        "private_consolidated": 0,
        "private_matched": 0,
        "private_new": 0,
        "private_skipped_insufficient_context": 0,
        "private_skipped_conflict": 0,
    }

    bundle_index = build_bundle_index(elements)
    relation_neighbors = build_relation_neighbors(relations)

    for element in elements:
        counters["observed_elements"] += 1
        scope = classify_scope(element)
        decided_at = element.observed_at
        normalized_hostname = normalize_text(element.observed_hostname)
        normalized_ptr = normalize_text(element.observed_ptr)
        selected_hostname, hostname_issue = preferred_hostname(element)

        if scope == "private":
            handle_private_observation(
                conn,
                element=element,
                decided_at=decided_at,
                bundle_index=bundle_index,
                relation_neighbors=relation_neighbors,
                counters=counters,
            )
            continue

        canonical_ip = extract_ip_value(element.observed_ip)
        if canonical_ip is None:
            if hostname_issue == "hostname_ptr_conflict":
                counters["hostname_skipped_conflict"] += 1
                decision_type = "skipped_hostname_conflict"
                reasoning_summary = "hostname e PTR fortes divergiram entre si; consolidação adiada para evitar merge ambíguo."
                decision_payload = {
                    "identity_decision_id": f"iddec-{element.observed_element_id}",
                    "observed_element_id": element.observed_element_id,
                    "run_id": element.run_id,
                    "bundle_id": element.bundle_id,
                    "decision_type": decision_type,
                    "matched_element_id": None,
                    "new_element_id": None,
                    "confidence": confidence_for(decision_type),
                    "reasoning_summary": reasoning_summary,
                    "evidence_json": {
                        "observed_ip": None,
                        "observed_hostname": normalized_hostname,
                        "observed_ptr": normalized_ptr,
                        "selected_hostname": selected_hostname,
                        "source_type": element.source_type,
                        "scope": scope,
                        "rule": "hostname_ptr_conflict",
                    },
                    "decided_at": decided_at,
                }
                upsert_decision(conn, decision_payload)
                continue

            if selected_hostname is None:
                counters["hostname_skipped_weak"] += 1
                decision_type = "skipped_hostname_weak"
                reasoning_summary = "observação pública sem IP canônico e sem hostname/PTR forte o bastante para consolidar nesta rodada."
                decision_payload = {
                    "identity_decision_id": f"iddec-{element.observed_element_id}",
                    "observed_element_id": element.observed_element_id,
                    "run_id": element.run_id,
                    "bundle_id": element.bundle_id,
                    "decision_type": decision_type,
                    "matched_element_id": None,
                    "new_element_id": None,
                    "confidence": confidence_for(decision_type),
                    "reasoning_summary": reasoning_summary,
                    "evidence_json": {
                        "observed_ip": None,
                        "observed_hostname": normalized_hostname,
                        "observed_ptr": normalized_ptr,
                        "selected_hostname": None,
                        "source_type": element.source_type,
                        "scope": scope,
                        "rule": "hostname_ptr_weak",
                    },
                    "decided_at": decided_at,
                }
                upsert_decision(conn, decision_payload)
                continue

            counters["hostname_consolidated"] += 1
            canonical_hostname = selected_hostname
            existing = load_network_element_by_hostname(conn, canonical_hostname)
            element_kind = element_kind_for(element, scope)
            role_hint_current = role_hint_for(element)
            canonical_label = canonical_hostname
            element_id = existing["element_id"] if existing else stable_id("network-element", canonical_hostname)
            confidence = confidence_for("matched_existing_entity" if existing else "new_entity_created")

            if existing:
                counters["hostname_matched"] += 1
                decision_type = "matched_existing_entity"
                reasoning_summary = "hostname/PTR forte já possuía entidade canônica própria; a observação reforça a identidade existente sem merge com IP."
                matched_element_id = existing["element_id"]
                new_element_id = None
                first_seen_at = existing["first_seen_at"]
            else:
                counters["hostname_new"] += 1
                decision_type = "new_entity_created"
                reasoning_summary = "observação pública sem IP canônico, mas com hostname/PTR forte o bastante para criar identidade canônica determinística."
                matched_element_id = None
                new_element_id = element_id
                first_seen_at = element.observed_at

            upsert_network_element(
                conn,
                element_id=element_id,
                canonical_label=canonical_label,
                element_kind=element_kind,
                ip_scope="public",
                canonical_ip=None,
                canonical_hostname=canonical_hostname,
                canonical_asn=normalize_text(element.observed_asn),
                canonical_org=normalize_text(element.observed_org),
                confidence_current=confidence,
                role_hint_current=role_hint_current,
                first_seen_at=first_seen_at,
                last_seen_at=element.observed_at,
            )

            decision_payload = {
                "identity_decision_id": f"iddec-{element.observed_element_id}",
                "observed_element_id": element.observed_element_id,
                "run_id": element.run_id,
                "bundle_id": element.bundle_id,
                "decision_type": decision_type,
                "matched_element_id": matched_element_id,
                "new_element_id": new_element_id,
                "confidence": confidence,
                "reasoning_summary": reasoning_summary,
                "evidence_json": {
                    "observed_ip": None,
                    "observed_hostname": normalized_hostname,
                    "observed_ptr": normalized_ptr,
                    "selected_hostname": canonical_hostname,
                    "source_type": element.source_type,
                    "scope": scope,
                    "element_kind": element_kind,
                    "rule": "hostname_ptr_canonical_match",
                    "matched_existing": existing is not None,
                },
                "decided_at": decided_at,
            }
            upsert_decision(conn, decision_payload)
            continue

        existing = load_network_element_by_ip(conn, canonical_ip)
        canonical_hostname = None
        if existing and existing["canonical_hostname"] is not None:
            canonical_hostname = existing["canonical_hostname"]
        else:
            if selected_hostname is not None:
                canonical_hostname = selected_hostname

        element_kind = element_kind_for(element, scope)
        role_hint_current = role_hint_for(element)
        confidence = confidence_for("matched_existing_entity" if existing else "new_entity_created")
        canonical_label = canonical_ip
        element_id = existing["element_id"] if existing else stable_id("network-element", canonical_ip)

        if existing:
            counters["public_ip_matched"] += 1
            counters["public_ip_consolidated"] += 1
            decision_type = "matched_existing_entity"
            reasoning_summary = "IP público já possuía entidade canônica; a observação reforça a identidade existente sem merge semântico."
            matched_element_id = existing["element_id"]
            new_element_id = None
        else:
            counters["public_ip_new"] += 1
            counters["public_ip_consolidated"] += 1
            decision_type = "new_entity_created"
            reasoning_summary = "IP público novo sem correspondência canônica anterior; entidade criada de forma determinística por canonical_ip."
            matched_element_id = None
            new_element_id = element_id

        upsert_network_element(
            conn,
            element_id=element_id,
            canonical_label=canonical_label,
            element_kind=element_kind,
            ip_scope="public",
            canonical_ip=canonical_ip,
            canonical_hostname=canonical_hostname,
            canonical_asn=normalize_text(element.observed_asn),
            canonical_org=normalize_text(element.observed_org),
            confidence_current=confidence,
            role_hint_current=role_hint_current,
            first_seen_at=element.observed_at if not existing else existing["first_seen_at"],
            last_seen_at=element.observed_at,
        )

        decision_payload = {
            "identity_decision_id": f"iddec-{element.observed_element_id}",
            "observed_element_id": element.observed_element_id,
            "run_id": element.run_id,
            "bundle_id": element.bundle_id,
            "decision_type": decision_type,
            "matched_element_id": matched_element_id,
            "new_element_id": new_element_id,
            "confidence": confidence,
            "reasoning_summary": reasoning_summary,
            "evidence_json": {
                "observed_ip": element.observed_ip,
                "canonical_ip": canonical_ip,
                "observed_hostname": normalized_hostname,
                "observed_ptr": normalized_ptr,
                "selected_hostname": canonical_hostname,
                "observed_asn": normalize_text(element.observed_asn),
                "observed_org": normalize_text(element.observed_org),
                "source_type": element.source_type,
                "scope": scope,
                "element_kind": element_kind,
                "rule": "canonical_ip_public_match",
                "matched_existing": existing is not None,
            },
            "decided_at": decided_at,
        }
        upsert_decision(conn, decision_payload)

    return counters


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Consolida observações públicas mínimas em entidades canônicas")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"), help="DSN do PostgreSQL")
    parser.add_argument("--run-id", help="processa um run específico")
    parser.add_argument("--bundle-id", help="processa um bundle específico")
    parser.add_argument("--all-unconsolidated", action="store_true", help="processa todas as observações sem identity_decision")
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    if not args.database_url:
        raise ConsolidationError("DATABASE_URL não definido")

    require_args(args)

    with db_connect(args.database_url) as conn:
        elements = load_observed_elements(conn, args)
        relations = load_observed_relations(conn, args)
        if not elements:
            print(json.dumps({"status": "noop", "message": "nenhuma observed_element encontrada"}, ensure_ascii=False))
            return 0

        summary = consolidate(conn, elements, relations)
        conn.commit()

    print(json.dumps({"status": "ok", **summary}, ensure_ascii=False, default=str, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ConsolidationError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
