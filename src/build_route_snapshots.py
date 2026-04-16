#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Any

import psycopg


class RouteSnapshotError(RuntimeError):
    pass


@dataclass(frozen=True)
class RunContext:
    run_id: str
    bundle_id: str
    target_value: str
    scenario: str


def db_connect(database_url: str) -> psycopg.Connection[Any]:
    return psycopg.connect(database_url)


def load_run_context(conn: psycopg.Connection[Any], run_id: str) -> RunContext:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT run_id, target_value, scenario
            FROM topomemory.run
            WHERE run_id = %s
            """,
            (run_id,),
        )
        run_row = cur.fetchone()
    if run_row is None:
        raise RouteSnapshotError(f"run não encontrado: {run_id}")

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT bundle_id
            FROM topomemory.ingestion_bundle
            WHERE run_id = %s
            """,
            (run_id,),
        )
        bundle_row = cur.fetchone()
    if bundle_row is None:
        raise RouteSnapshotError(f"bundle não encontrado para run: {run_id}")

    return RunContext(run_id=run_row[0], bundle_id=bundle_row[0], target_value=run_row[1], scenario=run_row[2])


def load_run_elements(conn: psycopg.Connection[Any], run_id: str) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              run_id,
              bundle_id,
              observed_element_id,
              element_index,
              observed_ip,
              observed_hostname,
              observed_ptr,
              observed_ip_scope,
              hop_index,
              service_context,
              decision_type,
              confidence,
              reasoning_summary,
              matched_element_id,
              new_element_id,
              resolved_element_id,
              comparison_basis,
              comparison_key,
              observational_signature,
              resolved_ip_scope,
              observed_at,
              canonical_ip,
              canonical_hostname,
              canonical_asn,
              canonical_org,
              role_hint_current,
              first_seen_at,
              last_seen_at
            FROM topomemory.v_layer1_run_elements
            WHERE run_id = %s
            ORDER BY element_index
            """,
            (run_id,),
        )
        rows = cur.fetchall()

    columns = [
        "run_id",
        "bundle_id",
        "observed_element_id",
        "element_index",
        "observed_ip",
        "observed_hostname",
        "observed_ptr",
        "observed_ip_scope",
        "hop_index",
        "service_context",
        "decision_type",
        "confidence",
        "reasoning_summary",
        "matched_element_id",
        "new_element_id",
        "resolved_element_id",
        "comparison_basis",
        "comparison_key",
        "observational_signature",
        "resolved_ip_scope",
        "observed_at",
        "canonical_ip",
        "canonical_hostname",
        "canonical_asn",
        "canonical_org",
        "role_hint_current",
        "first_seen_at",
        "last_seen_at",
    ]
    return [dict(zip(columns, row, strict=True)) for row in rows]


def count_relations(conn: psycopg.Connection[Any], run_id: str) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM topomemory.observed_relation WHERE run_id = %s", (run_id,))
        return int(cur.fetchone()[0])


def canonical_label(row: dict[str, Any]) -> str:
    for key in ("canonical_hostname", "canonical_ip", "observed_hostname", "observed_ip", "observed_ptr", "observed_element_id"):
        value = row.get(key)
        if value:
            return str(value)
    return "unknown"


def build_path_signature(rows: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for row in rows:
        parts.append(
            f"{row['element_index']}:{canonical_label(row)}:{row.get('observed_ip_scope') or 'unknown'}:{row.get('decision_type') or 'unclassified'}"
        )
    return " > ".join(parts)


def build_resolved_path_signature(rows: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for row in rows:
        resolved = row.get("resolved_element_id")
        if resolved:
            parts.append(str(resolved))
        else:
            parts.append(f"unresolved:{row['element_index']}:{row.get('observational_signature') or 'none'}")
    return " > ".join(parts)


def choose_destination(rows: list[dict[str, Any]]) -> tuple[str | None, str | None, str | None, str | None, str]:
    fallback: dict[str, Any] | None = None
    last_resolved: dict[str, Any] | None = None
    for row in rows:
        if not row.get("resolved_element_id"):
            continue
        last_resolved = row
        if str(row.get("role_hint_current") or "") == "destination":
            return (
                str(row.get("resolved_element_id")),
                canonical_label(row),
                row.get("canonical_ip"),
                row.get("canonical_hostname"),
                "destino explícito encontrado em role_hint_current",
            )
        if fallback is None:
            fallback = row

    if fallback is not None:
        return (
            str(fallback.get("resolved_element_id")),
            canonical_label(fallback),
            fallback.get("canonical_ip"),
            fallback.get("canonical_hostname"),
            "usado último elemento resolvido porque não havia role_hint_current=destination",
        )

    if last_resolved is not None:
        return (
            str(last_resolved.get("resolved_element_id")),
            canonical_label(last_resolved),
            last_resolved.get("canonical_ip"),
            last_resolved.get("canonical_hostname"),
            "usado último elemento resolvido disponível",
        )

    return None, None, None, None, "sem destino resolvido suficiente"


def upsert_snapshot(conn: psycopg.Connection[Any], payload: dict[str, Any]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO topomemory.route_snapshot (
              route_snapshot_id,
              run_id,
              bundle_id,
              target_value,
              scenario,
              total_observed_elements,
              total_observed_relations,
              total_resolved_elements,
              total_unresolved_elements,
              public_element_count,
              private_element_count,
              matched_existing_count,
              new_entity_count,
              skipped_count,
              path_signature,
              resolved_path_signature,
              destination_element_id,
              destination_label,
              destination_ip,
              destination_hostname,
              snapshot_notes
            )
            VALUES (
              %(route_snapshot_id)s,
              %(run_id)s,
              %(bundle_id)s,
              %(target_value)s,
              %(scenario)s,
              %(total_observed_elements)s,
              %(total_observed_relations)s,
              %(total_resolved_elements)s,
              %(total_unresolved_elements)s,
              %(public_element_count)s,
              %(private_element_count)s,
              %(matched_existing_count)s,
              %(new_entity_count)s,
              %(skipped_count)s,
              %(path_signature)s,
              %(resolved_path_signature)s,
              %(destination_element_id)s,
              %(destination_label)s,
              %(destination_ip)s,
              %(destination_hostname)s,
              %(snapshot_notes)s
            )
            ON CONFLICT (run_id) DO UPDATE SET
              bundle_id = EXCLUDED.bundle_id,
              target_value = EXCLUDED.target_value,
              scenario = EXCLUDED.scenario,
              total_observed_elements = EXCLUDED.total_observed_elements,
              total_observed_relations = EXCLUDED.total_observed_relations,
              total_resolved_elements = EXCLUDED.total_resolved_elements,
              total_unresolved_elements = EXCLUDED.total_unresolved_elements,
              public_element_count = EXCLUDED.public_element_count,
              private_element_count = EXCLUDED.private_element_count,
              matched_existing_count = EXCLUDED.matched_existing_count,
              new_entity_count = EXCLUDED.new_entity_count,
              skipped_count = EXCLUDED.skipped_count,
              path_signature = EXCLUDED.path_signature,
              resolved_path_signature = EXCLUDED.resolved_path_signature,
              destination_element_id = EXCLUDED.destination_element_id,
              destination_label = EXCLUDED.destination_label,
              destination_ip = EXCLUDED.destination_ip,
              destination_hostname = EXCLUDED.destination_hostname,
              snapshot_notes = EXCLUDED.snapshot_notes
            """,
            payload,
        )


def process_run(conn: psycopg.Connection[Any], run_id: str) -> dict[str, Any]:
    context = load_run_context(conn, run_id)
    rows = load_run_elements(conn, run_id)
    relation_count = count_relations(conn, run_id)
    if not rows:
        raise RouteSnapshotError(f"run sem elementos de rota: {run_id}")

    total_resolved = sum(1 for row in rows if row.get("resolved_element_id"))
    total_unresolved = len(rows) - total_resolved
    public_count = sum(1 for row in rows if str(row.get("resolved_ip_scope") or row.get("observed_ip_scope") or "").lower() == "public")
    private_count = sum(1 for row in rows if str(row.get("resolved_ip_scope") or row.get("observed_ip_scope") or "").lower() == "private")
    matched_count = sum(1 for row in rows if row.get("decision_type") == "matched_existing_entity")
    new_count = sum(1 for row in rows if row.get("decision_type") == "new_entity_created")
    skipped_count = sum(1 for row in rows if str(row.get("decision_type") or "").startswith("skipped_"))

    destination_element_id, destination_label, destination_ip, destination_hostname, destination_reason = choose_destination(rows)
    path_signature = build_path_signature(rows)
    resolved_path_signature = build_resolved_path_signature(rows)
    notes = [destination_reason]
    if destination_element_id is None:
        notes.insert(0, "destino não resolvido")
    if relation_count == 0:
        notes.append("sem observed_relations registradas para o run")

    payload = {
        "route_snapshot_id": f"route-snapshot-{context.run_id}",
        "run_id": context.run_id,
        "bundle_id": context.bundle_id,
        "target_value": context.target_value,
        "scenario": context.scenario,
        "total_observed_elements": len(rows),
        "total_observed_relations": relation_count,
        "total_resolved_elements": total_resolved,
        "total_unresolved_elements": total_unresolved,
        "public_element_count": public_count,
        "private_element_count": private_count,
        "matched_existing_count": matched_count,
        "new_entity_count": new_count,
        "skipped_count": skipped_count,
        "path_signature": path_signature,
        "resolved_path_signature": resolved_path_signature,
        "destination_element_id": destination_element_id,
        "destination_label": destination_label,
        "destination_ip": destination_ip,
        "destination_hostname": destination_hostname,
        "snapshot_notes": " | ".join(notes),
    }
    upsert_snapshot(conn, payload)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Constrói route_snapshot mínimos da Camada 2")
    parser.add_argument("--run-id", help="run_id único para processar")
    parser.add_argument("--all", action="store_true", help="processa todos os runs")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"), help="DSN do PostgreSQL")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.database_url:
        raise RouteSnapshotError("DATABASE_URL não definido")
    if bool(args.run_id) == bool(args.all):
        raise RouteSnapshotError("informe exatamente um entre --run-id e --all")

    with db_connect(args.database_url) as conn:
        if args.all:
            with conn.cursor() as cur:
                cur.execute("SELECT run_id FROM topomemory.run ORDER BY started_at")
                run_ids = [row[0] for row in cur.fetchall()]
        else:
            assert args.run_id is not None
            run_ids = [args.run_id]

        if not run_ids:
            raise RouteSnapshotError("nenhum run encontrado para processar")

        processed: list[dict[str, Any]] = []
        skipped: list[str] = []
        for run_id in run_ids:
            try:
                processed.append(process_run(conn, run_id))
            except RouteSnapshotError as exc:
                if args.all:
                    skipped.append(f"{run_id}: {exc}")
                    continue
                raise
        conn.commit()

    for row in processed:
        print(
            " | ".join(
                [
                    f"run_id={row['run_id']}",
                    f"target_value={row['target_value']}",
                    f"scenario={row['scenario']}",
                    f"observed={row['total_observed_elements']}",
                    f"resolved={row['total_resolved_elements']}",
                    f"destination={row['destination_element_id'] or 'none'}",
                ]
            )
        )
    print(f"route_snapshot_total={len(processed)}")
    if skipped:
        print(f"route_snapshot_skipped={len(skipped)}")
        for item in skipped:
            print(f"skipped={item}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RouteSnapshotError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
