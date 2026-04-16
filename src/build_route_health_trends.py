#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg.types.json import Jsonb


TREND_WINDOW_SIZE_DEFAULT = 3
ASSESSMENT_VERSION = "layer2-route-health-v1"


class RouteHealthTrendError(RuntimeError):
    pass


@dataclass(frozen=True)
class TrendRow:
    run_id: str
    snapshot_id: str
    assessment_id: str
    public_resolved_path_signature: str | None
    private_resolved_path_signature: str | None
    destination_stable_key: str | None
    health_status: str
    structural_status: str
    route_change_status: str
    started_at: Any


def db_connect(database_url: str) -> psycopg.Connection[Any]:
    return psycopg.connect(database_url)


def load_equivalent_groups(conn: psycopg.Connection[Any]) -> list[tuple[str, str]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT r.target_value, r.scenario
            FROM topomemory.route_snapshot rs
            JOIN topomemory.run r ON r.run_id = rs.run_id
            ORDER BY 1, 2
            """
        )
        return [(row[0], row[1]) for row in cur.fetchall()]


def load_trend_inputs(conn: psycopg.Connection[Any], *, target_value: str, scenario: str, window_size: int) -> list[TrendRow]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              rs.run_id,
              rs.route_snapshot_id,
              ra.route_health_assessment_id,
              rs.public_resolved_path_signature,
              rs.private_resolved_path_signature,
              rs.destination_stable_key,
              ra.health_status,
              ra.structural_status,
              ra.route_change_status,
              r.started_at
            FROM topomemory.route_snapshot rs
            JOIN topomemory.run r ON r.run_id = rs.run_id
            JOIN topomemory.route_health_assessment ra
              ON ra.route_snapshot_id = rs.route_snapshot_id
             AND ra.assessment_version = %s
            WHERE rs.target_value = %s
              AND rs.scenario = %s
            ORDER BY r.started_at DESC
            LIMIT %s
            """,
            (ASSESSMENT_VERSION, target_value, scenario, window_size),
        )
        rows = cur.fetchall()

    return [TrendRow(*row) for row in rows]


def status_counter(values: list[str]) -> dict[str, int]:
    return dict(Counter(values))


def classify_trend(rows: list[TrendRow]) -> tuple[str, str, str, str, str, dict[str, Any]]:
    if not rows:
        return "insufficient_context", "insufficient_context", "insufficient_context", "insufficient_context", "low", {
            "reason": "nenhum run equivalente com snapshot e assessment disponível",
        }

    if len(rows) < 2:
        evidence = {
            "reason": "menos de dois runs equivalentes; leitura agregada insuficiente",
            "public_signatures": [row.public_resolved_path_signature for row in rows],
            "private_signatures": [row.private_resolved_path_signature for row in rows],
            "destination_keys": [row.destination_stable_key for row in rows],
        }
        return "insufficient_context", "insufficient_context", "insufficient_context", "insufficient_context", "low", evidence

    public_signatures = [row.public_resolved_path_signature for row in rows]
    private_signatures = [row.private_resolved_path_signature for row in rows]
    destination_keys = [row.destination_stable_key for row in rows]
    health_statuses = [row.health_status for row in rows]
    structural_statuses = [row.structural_status for row in rows]
    route_change_statuses = [row.route_change_status for row in rows]

    public_non_null = [sig for sig in public_signatures if sig]
    private_non_null = [sig for sig in private_signatures if sig]
    destination_non_null = [key for key in destination_keys if key]

    public_stability_status = "insufficient_context"
    if len(public_non_null) == len(rows):
        public_stability_status = "stable" if len(set(public_non_null)) == 1 else "unstable"

    destination_stability_status = "insufficient_context"
    if len(destination_non_null) == len(rows):
        destination_stability_status = "stable" if len(set(destination_non_null)) == 1 else "changed"
    elif destination_non_null:
        destination_stability_status = "unknown"

    private_variation_status = "insufficient_context"
    if len(private_non_null) == len(rows):
        unique_private = len(set(private_non_null))
        if unique_private == 1:
            private_variation_status = "low_variation"
        elif public_stability_status == "stable" and destination_stability_status == "stable":
            private_variation_status = "oscillating"
        else:
            private_variation_status = "unstable"

    overall_trend_status = "insufficient_context"
    if "blocked" in health_statuses or "degraded" in health_statuses:
        overall_trend_status = "degrading"
    elif destination_stability_status == "changed":
        overall_trend_status = "degrading"
    elif public_stability_status == "unstable":
        overall_trend_status = "degrading"
    elif destination_stability_status == "stable" and public_stability_status == "stable" and private_variation_status == "low_variation":
        overall_trend_status = "stable"
    elif destination_stability_status == "stable" and public_stability_status == "stable" and private_variation_status == "oscillating":
        overall_trend_status = "oscillating"
    elif destination_stability_status == "unknown" or public_stability_status == "insufficient_context" or private_variation_status == "insufficient_context":
        overall_trend_status = "insufficient_context"
    else:
        overall_trend_status = "oscillating"

    confidence = "high"
    if overall_trend_status == "insufficient_context":
        confidence = "low"
    elif public_stability_status != "stable" or destination_stability_status != "stable":
        confidence = "medium"
    elif private_variation_status == "oscillating":
        confidence = "medium"

    if overall_trend_status == "degrading" and confidence == "high":
        confidence = "medium"

    evidence = {
        "run_ids": [row.run_id for row in reversed(rows)],
        "route_snapshot_ids": [row.snapshot_id for row in reversed(rows)],
        "route_health_assessment_ids": [row.assessment_id for row in reversed(rows)],
        "public_signatures": public_signatures,
        "private_signatures": private_signatures,
        "destination_keys": destination_keys,
        "health_status_counts": status_counter(health_statuses),
        "structural_status_counts": status_counter(structural_statuses),
        "route_change_status_counts": status_counter(route_change_statuses),
        "window_size": len(rows),
        "trend_window_size_requested": TREND_WINDOW_SIZE_DEFAULT,
    }

    return public_stability_status, private_variation_status, destination_stability_status, overall_trend_status, confidence, evidence


def upsert_trend(conn: psycopg.Connection[Any], payload: dict[str, Any]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO topomemory.route_health_trend (
              route_health_trend_id,
              target_value,
              scenario,
              trend_window_size,
              total_runs_considered,
              latest_run_id,
              latest_snapshot_id,
              latest_assessment_id,
              public_stability_status,
              private_variation_status,
              destination_stability_status,
              overall_trend_status,
              confidence,
              reasoning_summary,
              evidence_json
            )
            VALUES (
              %(route_health_trend_id)s,
              %(target_value)s,
              %(scenario)s,
              %(trend_window_size)s,
              %(total_runs_considered)s,
              %(latest_run_id)s,
              %(latest_snapshot_id)s,
              %(latest_assessment_id)s,
              %(public_stability_status)s,
              %(private_variation_status)s,
              %(destination_stability_status)s,
              %(overall_trend_status)s,
              %(confidence)s,
              %(reasoning_summary)s,
              %(evidence_json)s
            )
            ON CONFLICT (target_value, scenario, trend_window_size) DO UPDATE SET
              total_runs_considered = EXCLUDED.total_runs_considered,
              latest_run_id = EXCLUDED.latest_run_id,
              latest_snapshot_id = EXCLUDED.latest_snapshot_id,
              latest_assessment_id = EXCLUDED.latest_assessment_id,
              public_stability_status = EXCLUDED.public_stability_status,
              private_variation_status = EXCLUDED.private_variation_status,
              destination_stability_status = EXCLUDED.destination_stability_status,
              overall_trend_status = EXCLUDED.overall_trend_status,
              confidence = EXCLUDED.confidence,
              reasoning_summary = EXCLUDED.reasoning_summary,
              evidence_json = EXCLUDED.evidence_json
            """,
            {**payload, "evidence_json": Jsonb(payload["evidence_json"])},
        )


def build_trend(conn: psycopg.Connection[Any], *, target_value: str, scenario: str, window_size: int) -> dict[str, Any]:
    rows = load_trend_inputs(conn, target_value=target_value, scenario=scenario, window_size=window_size)
    public_stability_status, private_variation_status, destination_stability_status, overall_trend_status, confidence, evidence = classify_trend(rows)

    latest = rows[0] if rows else None
    if latest is None:
        raise RouteHealthTrendError(f"nenhum snapshot/assessment disponível para {target_value} / {scenario}")

    if len(rows) < 2:
        reasoning_summary = "menos de dois runs equivalentes; leitura agregada insuficiente"
    elif overall_trend_status == "stable":
        reasoning_summary = "destino estável, trecho público estável e variação privada baixa"
    elif overall_trend_status == "oscillating":
        reasoning_summary = "destino estável, trecho público estável e variação privada recorrente"
    elif overall_trend_status == "degrading":
        reasoning_summary = "há sinal consistente de degradação por mudança de saúde, destino ou trecho público"
    else:
        reasoning_summary = "contexto insuficiente para resumir tendência com honestidade"

    payload = {
        "route_health_trend_id": f"route-health-trend-{target_value}-{scenario}-{window_size}",
        "target_value": target_value,
        "scenario": scenario,
        "trend_window_size": window_size,
        "total_runs_considered": len(rows),
        "latest_run_id": latest.run_id,
        "latest_snapshot_id": latest.snapshot_id,
        "latest_assessment_id": latest.assessment_id,
        "public_stability_status": public_stability_status,
        "private_variation_status": private_variation_status,
        "destination_stability_status": destination_stability_status,
        "overall_trend_status": overall_trend_status,
        "confidence": confidence,
        "reasoning_summary": reasoning_summary,
        "evidence_json": evidence,
    }
    upsert_trend(conn, payload)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Constrói tendência temporal mínima da Camada 2")
    parser.add_argument("--target", help="target_value a agregar")
    parser.add_argument("--scenario", help="scenario a agregar")
    parser.add_argument("--all", action="store_true", help="processa todos os grupos equivalentes")
    parser.add_argument("--window-size", type=int, default=TREND_WINDOW_SIZE_DEFAULT, help="tamanho da janela equivalente")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"), help="DSN do PostgreSQL")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.database_url:
        raise RouteHealthTrendError("DATABASE_URL não definido")
    if bool(args.all) == bool(args.target or args.scenario):
        raise RouteHealthTrendError("informe --all ou --target junto com --scenario")
    if args.target and not args.scenario:
        raise RouteHealthTrendError("informe --scenario junto com --target")
    if args.window_size < 1:
        raise RouteHealthTrendError("--window-size precisa ser >= 1")

    with db_connect(args.database_url) as conn:
        if args.all:
            groups = load_equivalent_groups(conn)
        else:
            groups = [(args.target, args.scenario)]

        if not groups:
            raise RouteHealthTrendError("nenhum grupo equivalente encontrado")

        processed: list[dict[str, Any]] = []
        for target_value, scenario in groups:
            try:
                processed.append(
                    build_trend(conn, target_value=target_value, scenario=scenario, window_size=args.window_size)
                )
            except RouteHealthTrendError as exc:
                if args.all:
                    print(f"skipped={target_value}/{scenario}: {exc}")
                    continue
                raise
        conn.commit()

    for row in processed:
        print(
            " | ".join(
                [
                    f"target_value={row['target_value']}",
                    f"scenario={row['scenario']}",
                    f"total_runs_considered={row['total_runs_considered']}",
                    f"public_stability_status={row['public_stability_status']}",
                    f"private_variation_status={row['private_variation_status']}",
                    f"destination_stability_status={row['destination_stability_status']}",
                    f"overall_trend_status={row['overall_trend_status']}",
                    f"confidence={row['confidence']}",
                    f"reasoning_summary={row['reasoning_summary']}",
                ]
            )
        )
    print(f"route_health_trend_total={len(processed)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RouteHealthTrendError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
