#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass
from typing import Any

import psycopg


class AuditError(RuntimeError):
    pass


@dataclass(frozen=True)
class AuditRow:
    run_id: str
    bundle_id: str
    observed_element_id: str
    element_index: int
    observed_ip: str | None
    observed_hostname: str | None
    observed_ptr: str | None
    observed_ip_scope: str | None
    hop_index: int | None
    service_context: str | None
    decision_type: str | None
    confidence: float | None
    reasoning_summary: str | None
    matched_element_id: str | None
    new_element_id: str | None
    resolved_element_id: str | None
    ip_scope: str | None
    observed_at: Any
    canonical_ip: str | None
    canonical_hostname: str | None
    canonical_asn: str | None
    canonical_org: str | None
    role_hint_current: str | None
    first_seen_at: Any
    last_seen_at: Any


def db_connect(database_url: str) -> psycopg.Connection[Any]:
    return psycopg.connect(database_url)


def load_rows(conn: psycopg.Connection[Any], *, run_id: str | None, bundle_id: str | None) -> list[AuditRow]:
    if bool(run_id) == bool(bundle_id):
        raise AuditError("informe exatamente um entre --run-id e --bundle-id")

    where_clause = "run_id = %s" if run_id else "bundle_id = %s"
    lookup = run_id or bundle_id
    assert lookup is not None

    with conn.cursor() as cur:
        cur.execute(
            f"""
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
              ip_scope,
              observed_at,
              canonical_ip,
              canonical_hostname,
              canonical_asn,
              canonical_org,
              role_hint_current,
              first_seen_at,
              last_seen_at
            FROM topomemory.v_layer1_identity_audit
            WHERE {where_clause}
            ORDER BY element_index
            """,
            (lookup,),
        )
        rows = cur.fetchall()

    return [AuditRow(*row) for row in rows]


def summarize(rows: list[AuditRow]) -> dict[str, Any]:
    decision_counts = Counter(row.decision_type or "unclassified" for row in rows)
    skipped_counts = Counter(row.decision_type for row in rows if row.decision_type and row.decision_type.startswith("skipped_"))
    resolved_scope_counts = Counter(row.ip_scope or "unresolved" for row in rows)

    return {
        "total_observed_elements": len(rows),
        "matched_existing_entity": decision_counts.get("matched_existing_entity", 0),
        "new_entity_created": decision_counts.get("new_entity_created", 0),
        "skipped_total": sum(skipped_counts.values()),
        "skipped_by_type": dict(sorted(skipped_counts.items())),
        "public": resolved_scope_counts.get("public", 0),
        "private": resolved_scope_counts.get("private", 0),
        "unresolved": resolved_scope_counts.get("unresolved", 0),
    }


def print_summary(summary: dict[str, Any], *, run_id: str | None, bundle_id: str | None) -> None:
    header = run_id or bundle_id or "audit"
    print(f"alvo={header}")
    print(f"total_observed_elements={summary['total_observed_elements']}")
    print(f"matched_existing_entity={summary['matched_existing_entity']}")
    print(f"new_entity_created={summary['new_entity_created']}")
    print(f"skipped_total={summary['skipped_total']}")
    if summary["skipped_by_type"]:
        for decision_type, count in summary["skipped_by_type"].items():
            print(f"{decision_type}={count}")
    print(f"public={summary['public']}")
    print(f"private={summary['private']}")
    print(f"unresolved={summary['unresolved']}")


def print_rows(rows: list[AuditRow]) -> None:
    columns = [
        "element_index",
        "observed_element_id",
        "decision_type",
        "confidence",
        "observed_ip",
        "observed_hostname",
        "observed_ptr",
        "observed_ip_scope",
        "resolved_element_id",
        "ip_scope",
        "canonical_ip",
        "canonical_hostname",
        "canonical_asn",
        "canonical_org",
        "role_hint_current",
        "reasoning_summary",
    ]
    print("")
    print("\t".join(columns))
    for row in rows:
        print(
            "\t".join(
                "" if value is None else str(value)
                for value in (
                    row.element_index,
                    row.observed_element_id,
                    row.decision_type,
                    row.confidence,
                    row.observed_ip,
                    row.observed_hostname,
                    row.observed_ptr,
                    row.observed_ip_scope,
                    row.resolved_element_id,
                    row.ip_scope,
                    row.canonical_ip,
                    row.canonical_hostname,
                    row.canonical_asn,
                    row.canonical_org,
                    row.role_hint_current,
                    row.reasoning_summary,
                )
            )
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Relatório de auditoria da Camada 1 baseline")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run-id", help="run_id a auditar")
    group.add_argument("--bundle-id", help="bundle_id a auditar")
    parser.add_argument("--summary-only", action="store_true", help="imprime só o resumo agregado")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"), help="DSN do PostgreSQL")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.database_url:
        raise AuditError("DATABASE_URL não definido")

    with db_connect(args.database_url) as conn:
        rows = load_rows(conn, run_id=args.run_id, bundle_id=args.bundle_id)

    if not rows:
        target = args.run_id or args.bundle_id
        raise AuditError(f"nenhum registro encontrado na auditoria para {target}")

    summary = summarize(rows)

    if args.summary_only:
        print(json.dumps({"target": args.run_id or args.bundle_id, **summary}, ensure_ascii=False, indent=2, default=str))
    else:
        print_summary(summary, run_id=args.run_id, bundle_id=args.bundle_id)
        print_rows(rows)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AuditError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
