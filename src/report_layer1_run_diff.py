#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from dataclasses import dataclass
from typing import Any

import psycopg


class RunDiffError(RuntimeError):
    pass


@dataclass(frozen=True)
class RunElement:
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
    comparison_basis: str
    comparison_key: str
    observational_signature: str
    resolved_ip_scope: str | None
    observed_at: Any
    canonical_ip: str | None
    canonical_hostname: str | None
    canonical_asn: str | None
    canonical_org: str | None
    role_hint_current: str | None
    first_seen_at: Any
    last_seen_at: Any


@dataclass(frozen=True)
class RunSummary:
    run_id: str
    bundle_id: str
    total_observed_elements: int
    matched_existing_entity: int
    new_entity_created: int
    skipped_elements: int
    resolved_elements: int
    public_resolved_elements: int
    private_resolved_elements: int
    observation_sequence: str | None
    hop_sequence: str | None


def db_connect(database_url: str) -> psycopg.Connection[Any]:
    return psycopg.connect(database_url)


def load_run_summary(conn: psycopg.Connection[Any], run_id: str) -> RunSummary:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              run_id,
              bundle_id,
              total_observed_elements,
              matched_existing_entity,
              new_entity_created,
              skipped_elements,
              resolved_elements,
              public_resolved_elements,
              private_resolved_elements,
              observation_sequence,
              hop_sequence
            FROM topomemory.v_layer1_run_diff_summary
            WHERE run_id = %s
            """,
            (run_id,),
        )
        row = cur.fetchone()

    if row is None:
        raise RunDiffError(f"run não encontrado na diff summary: {run_id}")

    return RunSummary(*row)


def load_run_elements(conn: psycopg.Connection[Any], run_id: str) -> list[RunElement]:
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

    if not rows:
        raise RunDiffError(f"run sem elementos para diff: {run_id}")

    return [RunElement(*row) for row in rows]


def pair_stats(rows_a: list[RunElement], rows_b: list[RunElement]) -> dict[str, Any]:
    keys_a = [row.comparison_key for row in rows_a]
    keys_b = [row.comparison_key for row in rows_b]
    set_a = set(keys_a)
    set_b = set(keys_b)
    common = set_a & set_b
    only_a = set_a - set_b
    only_b = set_b - set_a

    resolved_a = {row.resolved_element_id for row in rows_a if row.resolved_element_id}
    resolved_b = {row.resolved_element_id for row in rows_b if row.resolved_element_id}
    common_resolved = resolved_a & resolved_b

    public_a = sum(1 for row in rows_a if row.resolved_ip_scope == "public")
    private_a = sum(1 for row in rows_a if row.resolved_ip_scope == "private")
    public_b = sum(1 for row in rows_b if row.resolved_ip_scope == "public")
    private_b = sum(1 for row in rows_b if row.resolved_ip_scope == "private")

    hop_a = [row.observed_ip for row in rows_a if row.hop_index is not None and row.observed_ip]
    hop_b = [row.observed_ip for row in rows_b if row.hop_index is not None and row.observed_ip]
    hop_common_prefix = 0
    for left, right in zip(hop_a, hop_b, strict=False):
        if left != right:
            break
        hop_common_prefix += 1

    path_a = keys_a
    path_b = keys_b
    path_common_prefix = 0
    for left, right in zip(path_a, path_b, strict=False):
        if left != right:
            break
        path_common_prefix += 1

    return {
        "observed_common": len(common),
        "observed_only_a": len(only_a),
        "observed_only_b": len(only_b),
        "network_common": len(common_resolved),
        "network_only_a": len(resolved_a - resolved_b),
        "network_only_b": len(resolved_b - resolved_a),
        "public_a": public_a,
        "private_a": private_a,
        "public_b": public_b,
        "private_b": private_b,
        "hop_common_prefix": hop_common_prefix,
        "path_common_prefix": path_common_prefix,
        "keys_common": sorted(common),
        "keys_only_a": sorted(only_a),
        "keys_only_b": sorted(only_b),
        "resolved_common": sorted(common_resolved),
        "resolved_only_a": sorted(resolved_a - resolved_b),
        "resolved_only_b": sorted(resolved_b - resolved_a),
        "hop_a": hop_a,
        "hop_b": hop_b,
        "path_a": path_a,
        "path_b": path_b,
    }


def print_summary(summary_a: RunSummary, summary_b: RunSummary, stats: dict[str, Any]) -> None:
    print(f"run_a={summary_a.run_id}")
    print(f"bundle_a={summary_a.bundle_id}")
    print(f"run_b={summary_b.run_id}")
    print(f"bundle_b={summary_b.bundle_id}")
    print(f"observed_total_a={summary_a.total_observed_elements}")
    print(f"observed_total_b={summary_b.total_observed_elements}")
    print(f"resolved_total_a={summary_a.resolved_elements}")
    print(f"resolved_total_b={summary_b.resolved_elements}")
    print(f"common_observed={stats['observed_common']}")
    print(f"only_a_observed={stats['observed_only_a']}")
    print(f"only_b_observed={stats['observed_only_b']}")
    print(f"common_network_elements={stats['network_common']}")
    print(f"only_a_network_elements={stats['network_only_a']}")
    print(f"only_b_network_elements={stats['network_only_b']}")
    print(f"public_a={stats['public_a']}")
    print(f"private_a={stats['private_a']}")
    print(f"public_b={stats['public_b']}")
    print(f"private_b={stats['private_b']}")
    print(f"hop_common_prefix={stats['hop_common_prefix']}")
    print(f"path_common_prefix={stats['path_common_prefix']}")

    observed_common_ratio_a = stats["observed_common"] / summary_a.total_observed_elements if summary_a.total_observed_elements else 0
    observed_common_ratio_b = stats["observed_common"] / summary_b.total_observed_elements if summary_b.total_observed_elements else 0
    hop_ratio_a = stats["hop_common_prefix"] / len(stats["hop_a"]) if stats["hop_a"] else 0
    hop_ratio_b = stats["hop_common_prefix"] / len(stats["hop_b"]) if stats["hop_b"] else 0
    stability_a = (observed_common_ratio_a + hop_ratio_a) / 2
    stability_b = (observed_common_ratio_b + hop_ratio_b) / 2
    diversity_a = (
        (stats["observed_only_a"] / summary_a.total_observed_elements if summary_a.total_observed_elements else 0)
        + (1 - hop_ratio_a)
    ) / 2
    diversity_b = (
        (stats["observed_only_b"] / summary_b.total_observed_elements if summary_b.total_observed_elements else 0)
        + (1 - hop_ratio_b)
    ) / 2

    if stability_a > stability_b:
        more_stable = summary_a.run_id
    elif stability_b > stability_a:
        more_stable = summary_b.run_id
    else:
        more_stable = "empate"

    if diversity_a > diversity_b:
        more_diverse = summary_a.run_id
    elif diversity_b > diversity_a:
        more_diverse = summary_b.run_id
    else:
        more_diverse = "empate"

    print(f"mais_estavel={more_stable}")
    print(f"mais_diverso={more_diverse}")

    if stats["observed_common"]:
        print("diferenca_principal=há interseção observacional, mas a identidade resolvida e/ou a ordem do caminho divergem")
    elif stats["hop_common_prefix"]:
        print("diferenca_principal=as identidades resolvidas divergem, mas a sequência de hops privados preserva prefixo comum")
    else:
        print("diferenca_principal=as duas coletas se distinguem desde o início da observação")


def print_keys(title: str, keys: list[str], limit: int = 20) -> None:
    print(title)
    for key in keys[:limit]:
        print(f"- {key}")
    if len(keys) > limit:
        print(f"- ... ({len(keys) - limit} a mais)")


def print_rows(title: str, rows: list[RunElement], *, show_resolved: bool = True) -> None:
    print(title)
    header = [
        "element_index",
        "comparison_key",
        "decision_type",
        "observed_ip",
        "observed_hostname",
        "observed_ptr",
        "hop_index",
        "resolved_element_id" if show_resolved else "observational_signature",
        "resolved_ip_scope",
        "role_hint_current",
    ]
    print("\t".join(header))
    for row in rows:
        print(
            "\t".join(
                "" if value is None else str(value)
                for value in (
                    row.element_index,
                    row.comparison_key,
                    row.decision_type,
                    row.observed_ip,
                    row.observed_hostname,
                    row.observed_ptr,
                    row.hop_index,
                    row.resolved_element_id if show_resolved else row.observational_signature,
                    row.resolved_ip_scope,
                    row.role_hint_current,
                )
            )
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Comparação analítica entre dois runs da Camada 1")
    parser.add_argument("--run-a", required=True, help="run_id do lado A")
    parser.add_argument("--run-b", required=True, help="run_id do lado B")
    parser.add_argument("--summary-only", action="store_true", help="imprime só o resumo agregado")
    parser.add_argument("--show-common", action="store_true", help="lista os elementos comuns")
    parser.add_argument("--show-unique", action="store_true", help="lista os elementos exclusivos")
    parser.add_argument("--show-path", action="store_true", help="mostra a sequência observada e a sequência de hops")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"), help="DSN do PostgreSQL")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.database_url:
        raise RunDiffError("DATABASE_URL não definido")

    with db_connect(args.database_url) as conn:
        summary_a = load_run_summary(conn, args.run_a)
        summary_b = load_run_summary(conn, args.run_b)
        rows_a = load_run_elements(conn, args.run_a)
        rows_b = load_run_elements(conn, args.run_b)

    stats = pair_stats(rows_a, rows_b)

    print_summary(summary_a, summary_b, stats)

    if args.summary_only:
        return 0

    if args.show_common:
        common_rows_a = [row for row in rows_a if row.comparison_key in stats["keys_common"]]
        common_rows_b = [row for row in rows_b if row.comparison_key in stats["keys_common"]]
        print_rows("common_run_a", common_rows_a)
        print_rows("common_run_b", common_rows_b)

    if args.show_unique:
        unique_rows_a = [row for row in rows_a if row.comparison_key in stats["keys_only_a"]]
        unique_rows_b = [row for row in rows_b if row.comparison_key in stats["keys_only_b"]]
        print_rows("unique_run_a", unique_rows_a)
        print_rows("unique_run_b", unique_rows_b)

    if args.show_path:
        print("")
        print("path_run_a")
        print(" > ".join(stats["path_a"]))
        print("path_run_b")
        print(" > ".join(stats["path_b"]))
        print(f"hop_prefix_common={stats['hop_common_prefix']}")
        print(f"path_prefix_common={stats['path_common_prefix']}")
        print("hop_run_a")
        print(" > ".join(stats["hop_a"]))
        print("hop_run_b")
        print(" > ".join(stats["hop_b"]))

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RunDiffError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
