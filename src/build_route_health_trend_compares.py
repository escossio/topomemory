#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from build_route_health_trends import RouteHealthTrendError, build_trend, db_connect, load_equivalent_groups


class RouteHealthTrendCompareError(RuntimeError):
    pass


def trend_score(status: str) -> int | None:
    order = {
        "stable": 2,
        "oscillating": 1,
        "degrading": 0,
    }
    return order.get(status)


def public_delta(current: dict[str, Any], previous: dict[str, Any]) -> str:
    cur = current["public_stability_status"]
    prev = previous["public_stability_status"]
    if "insufficient_context" in {cur, prev}:
        return "insufficient_context"
    if cur == prev:
        return "unchanged"
    if cur == "stable" and prev == "unstable":
        return "improved"
    if cur == "unstable" and prev == "stable":
        return "worsened"
    return "unchanged"


def private_delta(current: dict[str, Any], previous: dict[str, Any]) -> str:
    cur = current["private_variation_status"]
    prev = previous["private_variation_status"]
    if "insufficient_context" in {cur, prev}:
        return "insufficient_context"
    if cur == prev:
        return "unchanged"
    order = {
        "low_variation": 2,
        "oscillating": 1,
        "unstable": 0,
    }
    cur_score = order[cur]
    prev_score = order[prev]
    if cur_score > prev_score:
        return "improved"
    if cur_score < prev_score:
        return "worsened"
    return "unchanged"


def destination_delta(current: dict[str, Any], previous: dict[str, Any]) -> str:
    cur = current["destination_stability_status"]
    prev = previous["destination_stability_status"]
    if "insufficient_context" in {cur, prev}:
        return "insufficient_context"
    if "unknown" in {cur, prev}:
        return "unknown"
    if cur == "stable" and prev == "stable":
        if current["destination_stable_key"] and current["destination_stable_key"] == previous["destination_stable_key"]:
            return "stable"
        return "changed"
    if cur != prev:
        return "changed"
    return "changed"


def overall_delta(current: dict[str, Any], previous: dict[str, Any]) -> str:
    cur_score = trend_score(current["overall_trend_status"])
    prev_score = trend_score(previous["overall_trend_status"])
    if cur_score is None or prev_score is None:
        return "insufficient_context"
    if cur_score > prev_score:
        return "improving"
    if cur_score < prev_score:
        return "worsening"
    return "unchanged"


def confidence_for_compare(current: dict[str, Any], previous: dict[str, Any], deltas: dict[str, str]) -> str:
    if any(value == "insufficient_context" for value in deltas.values()):
        return "low"
    if current["total_runs_considered"] == 1 and previous["total_runs_considered"] == 1:
        return "medium"
    return "high"


def compare_reasoning(deltas: dict[str, str]) -> str:
    if deltas["overall_trend_delta"] == "insufficient_context":
        return "contexto insuficiente para comparar janelas sucessivas com honestidade"
    public_phrase = {
        "improved": "delta público melhorou",
        "unchanged": "delta público permaneceu estável",
        "worsened": "delta público piorou",
        "insufficient_context": "delta público sem contexto suficiente",
    }[deltas["public_trend_delta"]]
    private_phrase = {
        "improved": "delta privado melhorou",
        "unchanged": "delta privado permaneceu no mesmo patamar",
        "worsened": "delta privado piorou",
        "insufficient_context": "delta privado sem contexto suficiente",
    }[deltas["private_trend_delta"]]
    destination_phrase = {
        "stable": "destino permaneceu estável",
        "changed": "destino mudou",
        "unknown": "destino ficou ambíguo",
        "insufficient_context": "destino sem contexto suficiente",
    }[deltas["destination_trend_delta"]]
    overall_phrase = {
        "improving": "tendência geral melhorou",
        "unchanged": "tendência geral permaneceu equivalente",
        "worsening": "tendência geral piorou",
        "insufficient_context": "tendência geral sem contexto suficiente",
    }[deltas["overall_trend_delta"]]
    return f"{public_phrase}; {private_phrase}; {destination_phrase}; {overall_phrase}"


def upsert_compare(conn: psycopg.Connection[Any], payload: dict[str, Any]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO topomemory.route_health_trend_compare (
              route_health_trend_compare_id,
              target_value,
              scenario,
              current_trend_id,
              previous_trend_id,
              current_window_size,
              previous_window_size,
              public_trend_delta,
              private_trend_delta,
              destination_trend_delta,
              overall_trend_delta,
              confidence,
              reasoning_summary,
              evidence_json
            )
            VALUES (
              %(route_health_trend_compare_id)s,
              %(target_value)s,
              %(scenario)s,
              %(current_trend_id)s,
              %(previous_trend_id)s,
              %(current_window_size)s,
              %(previous_window_size)s,
              %(public_trend_delta)s,
              %(private_trend_delta)s,
              %(destination_trend_delta)s,
              %(overall_trend_delta)s,
              %(confidence)s,
              %(reasoning_summary)s,
              %(evidence_json)s
            )
            ON CONFLICT (target_value, scenario, current_trend_id, previous_trend_id) DO UPDATE SET
              current_window_size = EXCLUDED.current_window_size,
              previous_window_size = EXCLUDED.previous_window_size,
              public_trend_delta = EXCLUDED.public_trend_delta,
              private_trend_delta = EXCLUDED.private_trend_delta,
              destination_trend_delta = EXCLUDED.destination_trend_delta,
              overall_trend_delta = EXCLUDED.overall_trend_delta,
              confidence = EXCLUDED.confidence,
              reasoning_summary = EXCLUDED.reasoning_summary,
              evidence_json = EXCLUDED.evidence_json
            """,
            {**payload, "evidence_json": Jsonb(payload["evidence_json"])},
        )


def compare_trends(current: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    deltas = {
        "public_trend_delta": public_delta(current, previous),
        "private_trend_delta": private_delta(current, previous),
        "destination_trend_delta": destination_delta(current, previous),
        "overall_trend_delta": overall_delta(current, previous),
    }
    confidence = confidence_for_compare(current, previous, deltas)
    reasoning_summary = compare_reasoning(deltas)
    evidence = {
        "current_trend_id": current["route_health_trend_id"],
        "previous_trend_id": previous["route_health_trend_id"],
        "current_statuses": {
            "public_stability_status": current["public_stability_status"],
            "private_variation_status": current["private_variation_status"],
            "destination_stability_status": current["destination_stability_status"],
            "overall_trend_status": current["overall_trend_status"],
            "confidence": current["confidence"],
        },
        "previous_statuses": {
            "public_stability_status": previous["public_stability_status"],
            "private_variation_status": previous["private_variation_status"],
            "destination_stability_status": previous["destination_stability_status"],
            "overall_trend_status": previous["overall_trend_status"],
            "confidence": previous["confidence"],
        },
        "current_window_run_ids": current["evidence_json"].get("run_ids", []),
        "previous_window_run_ids": previous["evidence_json"].get("run_ids", []),
        "current_public_signatures": current["evidence_json"].get("public_signatures", []),
        "previous_public_signatures": previous["evidence_json"].get("public_signatures", []),
        "current_private_signatures": current["evidence_json"].get("private_signatures", []),
        "previous_private_signatures": previous["evidence_json"].get("private_signatures", []),
        "current_destination_keys": current["evidence_json"].get("destination_keys", []),
        "previous_destination_keys": previous["evidence_json"].get("destination_keys", []),
    }
    payload = {
        "route_health_trend_compare_id": f"route-health-trend-compare-{current['route_health_trend_id']}-{previous['route_health_trend_id']}",
        "target_value": current["target_value"],
        "scenario": current["scenario"],
        "current_trend_id": current["route_health_trend_id"],
        "previous_trend_id": previous["route_health_trend_id"],
        "current_window_size": current["trend_window_size"],
        "previous_window_size": previous["trend_window_size"],
        **deltas,
        "confidence": confidence,
        "reasoning_summary": reasoning_summary,
        "evidence_json": evidence,
    }
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Constrói comparação mínima entre janelas sucessivas da Camada 2")
    parser.add_argument("--target", help="target_value a comparar")
    parser.add_argument("--scenario", help="scenario a comparar")
    parser.add_argument("--all", action="store_true", help="processa todos os grupos equivalentes")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"), help="DSN do PostgreSQL")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.database_url:
        raise RouteHealthTrendCompareError("DATABASE_URL não definido")
    if bool(args.all) == bool(args.target or args.scenario):
        raise RouteHealthTrendCompareError("informe --all ou --target junto com --scenario")
    if args.target and not args.scenario:
        raise RouteHealthTrendCompareError("informe --scenario junto com --target")

    with db_connect(args.database_url) as conn:
        if args.all:
            groups = load_equivalent_groups(conn)
        else:
            groups = [(args.target, args.scenario)]

        if not groups:
            raise RouteHealthTrendCompareError("nenhum grupo equivalente encontrado")

        processed: list[dict[str, Any]] = []
        for target_value, scenario in groups:
            try:
                current = build_trend(conn, target_value=target_value, scenario=scenario, window_size=1, window_offset=0)
                previous = build_trend(conn, target_value=target_value, scenario=scenario, window_size=1, window_offset=1)
                payload = compare_trends(current, previous)
                upsert_compare(conn, payload)
                processed.append(payload)
            except RouteHealthTrendError as exc:
                if args.all:
                    print(f"skipped={target_value}/{scenario}: {exc}")
                    continue
                raise RouteHealthTrendCompareError(str(exc)) from exc
        conn.commit()

    for row in processed:
        print(
            " | ".join(
                [
                    f"target_value={row['target_value']}",
                    f"scenario={row['scenario']}",
                    f"current_trend_id={row['current_trend_id']}",
                    f"previous_trend_id={row['previous_trend_id']}",
                    f"public_trend_delta={row['public_trend_delta']}",
                    f"private_trend_delta={row['private_trend_delta']}",
                    f"destination_trend_delta={row['destination_trend_delta']}",
                    f"overall_trend_delta={row['overall_trend_delta']}",
                    f"confidence={row['confidence']}",
                    f"reasoning_summary={row['reasoning_summary']}",
                ]
            )
        )
    print(f"route_health_trend_compare_total={len(processed)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RouteHealthTrendCompareError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
