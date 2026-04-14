#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


@dataclass(frozen=True)
class ObservedElement:
    observed_element_id: str
    bundle_id: str
    run_id: str
    element_index: int
    observed_ip: str | None
    observed_hostname: str | None
    observed_asn: str | None
    observed_org: str | None
    source_type: str
    observed_at: datetime
    raw_json: dict[str, Any]
    target_type: str
    target_value: str
    service_hint: str
    scenario: str


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


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


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
            {
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
            },
        )


def upsert_decision(conn: psycopg.Connection[Any], payload: dict[str, Any]) -> None:
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


def consolidate(conn: psycopg.Connection[Any], elements: list[ObservedElement]) -> dict[str, int]:
    counters = {
        "observed_elements": 0,
        "public_consolidated": 0,
        "public_matched": 0,
        "public_new": 0,
        "private_skipped": 0,
        "hostname_deferred": 0,
    }

    for element in elements:
        counters["observed_elements"] += 1
        scope = classify_scope(element)
        decided_at = element.observed_at
        normalized_hostname = normalize_text(element.observed_hostname)

        if scope == "private":
            counters["private_skipped"] += 1
            decision_type = "skipped_private_scope"
            reasoning_summary = "observação em escopo privado ou reservado; consolidação automática adiada para etapa posterior."
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
                    "source_type": element.source_type,
                    "scope": scope,
                    "rule": "private_scope_skipped",
                },
                "decided_at": decided_at,
            }
            upsert_decision(conn, decision_payload)
            continue

        if not element.observed_ip:
            counters["hostname_deferred"] += 1
            decision_type = "skipped_no_public_ip"
            reasoning_summary = "observação pública sem IP canônico determinístico; a consolidação desta rodada é somente por IP público."
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
                    "source_type": element.source_type,
                    "scope": scope,
                    "rule": "hostname_only_deferred",
                },
                "decided_at": decided_at,
            }
            upsert_decision(conn, decision_payload)
            continue

        canonical_ip = canonicalize_ip(element.observed_ip)
        existing = load_network_element_by_ip(conn, canonical_ip)
        canonical_hostname = None
        if existing and existing["canonical_hostname"] is not None:
            canonical_hostname = existing["canonical_hostname"]
        elif normalized_hostname and element.source_type == "target":
            canonical_hostname = normalized_hostname

        element_kind = element_kind_for(element, scope)
        role_hint_current = role_hint_for(element)
        confidence = confidence_for("matched_existing_entity" if existing else "new_entity_created")
        canonical_label = canonical_ip if not canonical_hostname else canonical_hostname
        element_id = existing["element_id"] if existing else stable_id("network-element", canonical_ip)

        if existing:
            counters["public_matched"] += 1
            counters["public_consolidated"] += 1
            decision_type = "matched_existing_entity"
            reasoning_summary = "IP público já possuía entidade canônica; a observação reforça a identidade existente sem merge semântico."
            matched_element_id = existing["element_id"]
            new_element_id = None
        else:
            counters["public_new"] += 1
            counters["public_consolidated"] += 1
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
        if not elements:
            print(json.dumps({"status": "noop", "message": "nenhuma observed_element encontrada"}, ensure_ascii=False))
            return 0

        summary = consolidate(conn, elements)
        conn.commit()

    print(json.dumps({"status": "ok", **summary}, ensure_ascii=False, default=str, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ConsolidationError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
