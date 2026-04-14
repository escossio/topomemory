#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.types.json import Jsonb


class ExpansionError(Exception):
    pass


def parse_timestamp(value: str, field_name: str) -> datetime:
    candidate = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ExpansionError(f"timestamp inválido em {field_name}: {value}") from exc
    if parsed.tzinfo is None:
        raise ExpansionError(f"timestamp {field_name} precisa ter timezone explícito")
    return parsed


def require_list(data: dict[str, Any], key: str, source: str) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ExpansionError(f"{source} precisa conter lista '{key}'")
    return value


def require_mapping(data: dict[str, Any], key: str, source: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ExpansionError(f"{source} precisa conter objeto '{key}'")
    return value


def require_text(data: dict[str, Any], key: str, source: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ExpansionError(f"{source} precisa conter texto não vazio em '{key}'")
    return value.strip()


def normalize_json(value: Any) -> Any:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return value
        return parsed
    return value


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip())
    return cleaned.strip("-").lower() or "item"


def is_ip_like(value: str) -> bool:
    return bool(re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", value) or ":" in value)


def infer_ip_scope(value: str | None) -> str | None:
    if not value:
        return None
    if re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", value):
        return "ipv4"
    if ":" in value:
        return "ipv6"
    return "hostname"


def infer_hop_index(label: str | None) -> int | None:
    if not label:
        return None
    match = re.match(r"hop\s+(\d+)\b", label.strip(), re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def db_connect(database_url: str) -> psycopg.Connection[Any]:
    return psycopg.connect(database_url)


def load_bundle(conn: psycopg.Connection[Any], *, run_id: str | None, bundle_id: str | None) -> dict[str, Any]:
    if not run_id and not bundle_id:
        raise ExpansionError("é obrigatório informar run_id ou bundle_id")

    where_clause = "run_id = %s" if run_id else "bundle_id = %s"
    lookup = run_id or bundle_id
    assert lookup is not None

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT bundle_id, run_id, bundle_version, run_context_json, observed_elements_json, observed_relations_json
            FROM topomemory.ingestion_bundle
            WHERE {where_clause}
            """,
            (lookup,),
        )
        row = cur.fetchone()

    if row is None:
        raise ExpansionError(f"bundle não encontrado para {where_clause}: {lookup}")

    bundle_id_db, run_id_db, bundle_version, run_context_json, observed_elements_json, observed_relations_json = row
    return {
        "bundle_id": bundle_id_db,
        "run_id": run_id_db,
        "bundle_version": bundle_version,
        "run_context": normalize_json(run_context_json),
        "observed_elements": normalize_json(observed_elements_json),
        "observed_relations": normalize_json(observed_relations_json),
    }


def element_payload(
    *,
    bundle_id: str,
    run_id: str,
    observed_at: datetime,
    element_index: int,
    element: dict[str, Any],
    service_context: str | None,
) -> dict[str, Any]:
    element_id = str(element.get("observation_id") or f"oe-{slugify(bundle_id)}-{element_index:04d}")
    label = element.get("label")
    element_type = str(element.get("element_type") or "unknown").strip()
    observed_ip = label if isinstance(label, str) and is_ip_like(label) else None
    observed_hostname = label if isinstance(label, str) and not is_ip_like(label) and element_type == "target" else None
    hop_index = infer_hop_index(label if isinstance(label, str) else None)
    source_type = element_type
    raw_json = element
    return {
        "observed_element_id": element_id,
        "bundle_id": bundle_id,
        "run_id": run_id,
        "element_index": element_index,
        "observed_ip": observed_ip,
        "observed_hostname": observed_hostname,
        "observed_ptr": None,
        "observed_asn": None,
        "observed_org": None,
        "ip_scope": infer_ip_scope(observed_ip or observed_hostname),
        "hop_index": hop_index,
        "service_context": service_context,
        "source_type": source_type,
        "observed_at": observed_at,
        "raw_json": raw_json,
    }


def relation_payload(
    *,
    bundle_id: str,
    run_id: str,
    relation_index: int,
    relation: dict[str, Any],
    element_index_by_id: dict[str, int],
) -> dict[str, Any]:
    relation_id = str(relation.get("relation_id") or f"or-{slugify(bundle_id)}-{relation_index:04d}")
    from_element_id = relation.get("from_element_id")
    to_element_id = relation.get("to_element_id")
    if not isinstance(from_element_id, str) or not isinstance(to_element_id, str):
        raise ExpansionError(f"relation {relation_index} sem from_element_id/to_element_id válidos")
    try:
        from_index = element_index_by_id[from_element_id]
    except KeyError as exc:
        raise ExpansionError(f"relation {relation_index} referencia from_element_id desconhecido: {from_element_id}") from exc
    try:
        to_index = element_index_by_id[to_element_id]
    except KeyError as exc:
        raise ExpansionError(f"relation {relation_index} referencia to_element_id desconhecido: {to_element_id}") from exc

    confidence = relation.get("confidence")
    confidence_hint = None
    if isinstance(confidence, (int, float)):
        confidence_hint = float(confidence)

    return {
        "observed_relation_id": relation_id,
        "bundle_id": bundle_id,
        "run_id": run_id,
        "relation_index": relation_index,
        "from_element_index": from_index,
        "to_element_index": to_index,
        "relation_type": str(relation.get("relation_type") or "unknown").strip(),
        "relation_order": relation_index,
        "confidence_hint": confidence_hint,
        "raw_json": relation,
    }


def upsert_element(conn: psycopg.Connection[Any], payload: dict[str, Any]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO topomemory.observed_element (
              observed_element_id,
              bundle_id,
              run_id,
              element_index,
              observed_ip,
              observed_hostname,
              observed_ptr,
              observed_asn,
              observed_org,
              ip_scope,
              hop_index,
              service_context,
              source_type,
              observed_at,
              raw_json
            )
            VALUES (
              %(observed_element_id)s,
              %(bundle_id)s,
              %(run_id)s,
              %(element_index)s,
              %(observed_ip)s,
              %(observed_hostname)s,
              %(observed_ptr)s,
              %(observed_asn)s,
              %(observed_org)s,
              %(ip_scope)s,
              %(hop_index)s,
              %(service_context)s,
              %(source_type)s,
              %(observed_at)s,
              %(raw_json)s
            )
            ON CONFLICT (bundle_id, element_index) DO UPDATE SET
              observed_element_id = EXCLUDED.observed_element_id,
              run_id = EXCLUDED.run_id,
              observed_ip = EXCLUDED.observed_ip,
              observed_hostname = EXCLUDED.observed_hostname,
              observed_ptr = EXCLUDED.observed_ptr,
              observed_asn = EXCLUDED.observed_asn,
              observed_org = EXCLUDED.observed_org,
              ip_scope = EXCLUDED.ip_scope,
              hop_index = EXCLUDED.hop_index,
              service_context = EXCLUDED.service_context,
              source_type = EXCLUDED.source_type,
              observed_at = EXCLUDED.observed_at,
              raw_json = EXCLUDED.raw_json,
              updated_at = now()
            """,
            {
                **payload,
                "raw_json": Jsonb(payload["raw_json"]),
            },
        )


def upsert_relation(conn: psycopg.Connection[Any], payload: dict[str, Any]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO topomemory.observed_relation (
              observed_relation_id,
              bundle_id,
              run_id,
              relation_index,
              from_element_index,
              to_element_index,
              relation_type,
              relation_order,
              confidence_hint,
              raw_json
            )
            VALUES (
              %(observed_relation_id)s,
              %(bundle_id)s,
              %(run_id)s,
              %(relation_index)s,
              %(from_element_index)s,
              %(to_element_index)s,
              %(relation_type)s,
              %(relation_order)s,
              %(confidence_hint)s,
              %(raw_json)s
            )
            ON CONFLICT (bundle_id, relation_index) DO UPDATE SET
              observed_relation_id = EXCLUDED.observed_relation_id,
              run_id = EXCLUDED.run_id,
              from_element_index = EXCLUDED.from_element_index,
              to_element_index = EXCLUDED.to_element_index,
              relation_type = EXCLUDED.relation_type,
              relation_order = EXCLUDED.relation_order,
              confidence_hint = EXCLUDED.confidence_hint,
              raw_json = EXCLUDED.raw_json,
              updated_at = now()
            """,
            {
                **payload,
                "raw_json": Jsonb(payload["raw_json"]),
            },
        )


def expand_bundle(conn: psycopg.Connection[Any], bundle: dict[str, Any]) -> dict[str, int]:
    run_context = require_mapping(bundle, "run_context", "bundle")
    service_context = run_context.get("service_hint")
    if not isinstance(service_context, str) or not service_context.strip():
        service_context = None
    observed_at_raw = require_text(run_context, "finished_at", "bundle.run_context")
    observed_at = parse_timestamp(observed_at_raw, "bundle.run_context.finished_at")

    observed_elements = require_list(bundle, "observed_elements", "bundle")
    observed_relations = require_list(bundle, "observed_relations", "bundle")
    bundle_id = require_text(bundle, "bundle_id", "bundle")
    run_id = require_text(bundle, "run_id", "bundle")

    element_index_by_id: dict[str, int] = {}
    for index, element in enumerate(observed_elements, start=1):
        if not isinstance(element, dict):
            raise ExpansionError(f"observed_elements[{index}] precisa ser um objeto")
        element_id = element.get("element_id")
        if not isinstance(element_id, str) or not element_id.strip():
            raise ExpansionError(f"observed_elements[{index}] sem element_id válido")
        if element_id in element_index_by_id:
            raise ExpansionError(f"element_id duplicado no bundle: {element_id}")
        element_index_by_id[element_id] = index
        upsert_element(
            conn,
            element_payload(
                bundle_id=bundle_id,
                run_id=run_id,
                observed_at=observed_at,
                element_index=index,
                element=element,
                service_context=service_context,
            ),
        )

    for index, relation in enumerate(observed_relations, start=1):
        if not isinstance(relation, dict):
            raise ExpansionError(f"observed_relations[{index}] precisa ser um objeto")
        upsert_relation(
            conn,
            relation_payload(
                bundle_id=bundle_id,
                run_id=run_id,
                relation_index=index,
                relation=relation,
                element_index_by_id=element_index_by_id,
            ),
        )

    return {"observed_element": len(observed_elements), "observed_relation": len(observed_relations)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Expande bundles da Camada 0 para a normalização mínima da Camada 1.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run-id", help="run_id do ingestion_bundle persistido")
    group.add_argument("--bundle-id", help="bundle_id do ingestion_bundle persistido")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="DSN do PostgreSQL; default usa DATABASE_URL do ambiente",
    )
    args = parser.parse_args()

    if not args.database_url:
        raise ExpansionError("DATABASE_URL não definido")

    with db_connect(args.database_url) as conn:
        with conn.transaction():
            bundle = load_bundle(conn, run_id=args.run_id, bundle_id=args.bundle_id)
            counts = expand_bundle(conn, bundle)

    identifier = args.run_id or args.bundle_id
    print(
        json.dumps(
            {
                "bundle_id": bundle["bundle_id"],
                "run_id": bundle["run_id"],
                "expanded": counts,
                "identifier": identifier,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ExpansionError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)
