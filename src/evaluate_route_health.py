#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg.types.json import Jsonb


ASSESSMENT_VERSION = "layer2-route-health-v1"


class RouteHealthError(RuntimeError):
    pass


@dataclass(frozen=True)
class SnapshotRow:
    route_snapshot_id: str
    run_id: str
    bundle_id: str
    target_value: str
    scenario: str
    total_observed_elements: int
    total_observed_relations: int
    total_resolved_elements: int
    total_unresolved_elements: int
    public_element_count: int
    private_element_count: int
    matched_existing_count: int
    new_entity_count: int
    skipped_count: int
    path_signature: str
    resolved_path_signature: str
    destination_element_id: str | None
    destination_label: str | None
    destination_ip: str | None
    destination_hostname: str | None
    snapshot_notes: str | None


def db_connect(database_url: str) -> psycopg.Connection[Any]:
    return psycopg.connect(database_url)


def load_snapshot(conn: psycopg.Connection[Any], run_id: str) -> SnapshotRow:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
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
            FROM topomemory.route_snapshot
            WHERE run_id = %s
            """,
            (run_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise RouteHealthError(f"route_snapshot ausente para run: {run_id}")
    return SnapshotRow(*row)


def load_run_meta(conn: psycopg.Connection[Any], run_id: str) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT run_id, target_value, scenario, run_status, collection_health
            FROM topomemory.run
            WHERE run_id = %s
            """,
            (run_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise RouteHealthError(f"run não encontrado: {run_id}")
    return {
        "run_id": row[0],
        "target_value": row[1],
        "scenario": row[2],
        "run_status": row[3],
        "collection_health": row[4],
    }


def find_previous_equivalent_snapshot(conn: psycopg.Connection[Any], *, target_value: str, scenario: str, run_id: str) -> SnapshotRow | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT rs.route_snapshot_id, rs.run_id, rs.bundle_id, rs.target_value, rs.scenario,
                   rs.total_observed_elements, rs.total_observed_relations, rs.total_resolved_elements, rs.total_unresolved_elements,
                   rs.public_element_count, rs.private_element_count, rs.matched_existing_count, rs.new_entity_count, rs.skipped_count,
                   rs.path_signature, rs.resolved_path_signature, rs.destination_element_id, rs.destination_label, rs.destination_ip, rs.destination_hostname, rs.snapshot_notes
            FROM topomemory.route_snapshot rs
            JOIN topomemory.run r ON r.run_id = rs.run_id
            WHERE rs.target_value = %s
              AND rs.scenario = %s
              AND rs.run_id <> %s
              AND r.started_at < (SELECT started_at FROM topomemory.run WHERE run_id = %s)
            ORDER BY r.started_at DESC
            LIMIT 1
            """,
            (target_value, scenario, run_id, run_id),
        )
        row = cur.fetchone()
    return SnapshotRow(*row) if row else None


def load_snapshot_by_run(conn: psycopg.Connection[Any], run_id: str) -> SnapshotRow | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT route_snapshot_id, run_id, bundle_id, target_value, scenario,
                   total_observed_elements, total_observed_relations, total_resolved_elements, total_unresolved_elements,
                   public_element_count, private_element_count, matched_existing_count, new_entity_count, skipped_count,
                   path_signature, resolved_path_signature, destination_element_id, destination_label, destination_ip, destination_hostname, snapshot_notes
            FROM topomemory.route_snapshot
            WHERE run_id = %s
            """,
            (run_id,),
        )
        row = cur.fetchone()
    return SnapshotRow(*row) if row else None


def choose_health(snapshot: SnapshotRow, run_meta: dict[str, Any]) -> tuple[str, str, str, str, dict[str, Any]]:
    total = snapshot.total_observed_elements
    resolved_ratio = snapshot.total_resolved_elements / total if total else 0.0
    destination_clear = bool(snapshot.destination_element_id)
    coherent_path = bool(snapshot.path_signature and snapshot.resolved_path_signature)

    evidence = {
        "total_observed_elements": snapshot.total_observed_elements,
        "total_resolved_elements": snapshot.total_resolved_elements,
        "total_unresolved_elements": snapshot.total_unresolved_elements,
        "public_element_count": snapshot.public_element_count,
        "private_element_count": snapshot.private_element_count,
        "matched_existing_count": snapshot.matched_existing_count,
        "new_entity_count": snapshot.new_entity_count,
        "skipped_count": snapshot.skipped_count,
        "path_signature": snapshot.path_signature,
        "resolved_path_signature": snapshot.resolved_path_signature,
    }

    if run_meta["run_status"] == "failed" or run_meta["collection_health"] == "blocked":
        return "blocked", "insufficient_context", "not_comparable", "low", evidence

    if run_meta["run_status"] == "success" and run_meta["collection_health"] == "healthy" and destination_clear and resolved_ratio >= 0.6 and coherent_path:
        confidence = "high" if resolved_ratio >= 0.85 else "medium"
        return "healthy", "stable", "first_observation", confidence, evidence

    if run_meta["run_status"] in {"success", "partial"} and (snapshot.total_resolved_elements > 0 or destination_clear):
        confidence = "medium" if resolved_ratio >= 0.35 else "low"
        structural_status = "changed" if resolved_ratio >= 0.5 else "insufficient_context"
        return "degraded", structural_status, "first_observation", confidence, evidence

    return "unknown", "insufficient_context", "not_comparable", "low", evidence


def classify_comparison(
    current: SnapshotRow,
    previous: SnapshotRow | None,
    structural_status: str,
    confidence: str,
    evidence: dict[str, Any],
) -> tuple[str, str, str, dict[str, Any], str]:
    if previous is None:
        evidence["compared_to_run_id"] = None
        evidence["compared_to_resolved_path_signature"] = None
        evidence["compared_to_snapshot_id"] = None
        return "first_observation", "insufficient_context", confidence, evidence, "primeira observação equivalente disponível"

    evidence["compared_to_run_id"] = previous.run_id
    evidence["compared_to_resolved_path_signature"] = previous.resolved_path_signature
    evidence["compared_to_snapshot_id"] = previous.route_snapshot_id
    if current.resolved_path_signature == previous.resolved_path_signature:
        return "unchanged", "stable", confidence, evidence, "rota resolvida estável em comparação com o run equivalente anterior"

    if current.resolved_path_signature and previous.resolved_path_signature:
        next_confidence = confidence if confidence != "low" else "medium"
        return "changed", "changed", next_confidence, evidence, "assinatura resolvida mudou entre runs equivalentes"

    return "not_comparable", "insufficient_context", "low", evidence, "comparação limitada por contexto insuficiente"


def upsert_assessment(conn: psycopg.Connection[Any], payload: dict[str, Any]) -> None:
    with conn.cursor() as cur:
        db_payload = {**payload, "evidence_json": Jsonb(payload["evidence_json"])}
        cur.execute(
            """
            INSERT INTO topomemory.route_health_assessment (
              route_health_assessment_id,
              route_snapshot_id,
              assessment_version,
              health_status,
              structural_status,
              route_change_status,
              confidence,
              reasoning_summary,
              evidence_json,
              compared_to_run_id,
              compared_to_snapshot_id
            )
            VALUES (
              %(route_health_assessment_id)s,
              %(route_snapshot_id)s,
              %(assessment_version)s,
              %(health_status)s,
              %(structural_status)s,
              %(route_change_status)s,
              %(confidence)s,
              %(reasoning_summary)s,
              %(evidence_json)s,
              %(compared_to_run_id)s,
              %(compared_to_snapshot_id)s
            )
            ON CONFLICT (route_snapshot_id, assessment_version) DO UPDATE SET
              health_status = EXCLUDED.health_status,
              structural_status = EXCLUDED.structural_status,
              route_change_status = EXCLUDED.route_change_status,
              confidence = EXCLUDED.confidence,
              reasoning_summary = EXCLUDED.reasoning_summary,
              evidence_json = EXCLUDED.evidence_json,
              compared_to_run_id = EXCLUDED.compared_to_run_id,
              compared_to_snapshot_id = EXCLUDED.compared_to_snapshot_id
            """,
            db_payload,
        )


def evaluate_run(conn: psycopg.Connection[Any], run_id: str, compare_to_run_id: str | None) -> dict[str, Any]:
    run_meta = load_run_meta(conn, run_id)
    snapshot = load_snapshot(conn, run_id)

    previous_snapshot: SnapshotRow | None = None
    if compare_to_run_id:
        previous_snapshot = load_snapshot(conn, compare_to_run_id)
    else:
        previous_snapshot = find_previous_equivalent_snapshot(
            conn,
            target_value=run_meta["target_value"],
            scenario=run_meta["scenario"],
            run_id=run_id,
        )

    health_status, structural_status, route_change_status, confidence, evidence = choose_health(snapshot, run_meta)
    if previous_snapshot is None:
        route_change_status = "first_observation" if compare_to_run_id is None else "not_comparable"
        reasoning_summary = "primeira observação equivalente disponível" if compare_to_run_id is None else "comparação solicitada, mas o snapshot comparativo não existe"
        evidence["compared_to_run_id"] = compare_to_run_id
        evidence["compared_to_snapshot_id"] = None
    else:
        route_change_status, structural_status, confidence, evidence, reasoning_summary = classify_comparison(
            snapshot, previous_snapshot, structural_status, confidence, evidence
        )

    payload = {
        "route_health_assessment_id": f"route-health-assessment-{snapshot.run_id}",
        "route_snapshot_id": snapshot.route_snapshot_id,
        "assessment_version": ASSESSMENT_VERSION,
        "health_status": health_status,
        "structural_status": structural_status,
        "route_change_status": route_change_status,
        "confidence": confidence,
        "reasoning_summary": reasoning_summary,
        "evidence_json": evidence,
        "compared_to_run_id": evidence.get("compared_to_run_id"),
        "compared_to_snapshot_id": evidence.get("compared_to_snapshot_id"),
    }
    upsert_assessment(conn, payload)
    return {
        **payload,
        "target_value": run_meta["target_value"],
        "scenario": run_meta["scenario"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Avalia a saúde mínima da rota da Camada 2")
    parser.add_argument("--run-id", required=True, help="run_id alvo")
    parser.add_argument("--compare-to-run-id", help="run_id comparativo explícito")
    parser.add_argument("--compare-to-previous-equivalent", action="store_true", help="usa automaticamente o run equivalente anterior mais recente")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"), help="DSN do PostgreSQL")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.database_url:
        raise RouteHealthError("DATABASE_URL não definido")
    if args.compare_to_run_id and args.compare_to_previous_equivalent:
        raise RouteHealthError("use apenas um modo de comparação")

    compare_to_run_id = args.compare_to_run_id if args.compare_to_run_id else None

    with db_connect(args.database_url) as conn:
        result = evaluate_run(conn, args.run_id, compare_to_run_id)
        conn.commit()

    print(
        " | ".join(
            [
                f"run_id={args.run_id}",
                f"target_value={result['target_value']}",
                f"scenario={result['scenario']}",
                f"health_status={result['health_status']}",
                f"structural_status={result['structural_status']}",
                f"route_change_status={result['route_change_status']}",
                f"confidence={result['confidence']}",
                f"reasoning_summary={result['reasoning_summary']}",
            ]
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RouteHealthError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
