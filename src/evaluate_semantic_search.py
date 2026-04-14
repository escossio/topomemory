#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

import psycopg

from embedding_provider import EMBEDDING_PROVIDER_ENV, EmbeddingProviderError, get_embedding_provider, vector_literal
from search_network_elements_semantic import search_elements


class SemanticEvalError(RuntimeError):
    pass


CATEGORY_PREDICATES = {
    "public_destination": lambda row: row["ip_scope"] == "public" and row["role_hint_current"] == "destination",
    "public_node": lambda row: row["ip_scope"] == "public" and row["element_kind"] == "public_node",
    "private_hop": lambda row: row["ip_scope"] == "private",
    "private_node": lambda row: row["ip_scope"] == "private",
}


@dataclass(frozen=True)
class QueryResult:
    query_id: str
    query_text: str
    category: str
    expected_match_mode: str
    expected_element_ids: list[str]
    expected_label_contains: list[str]
    expected_categories: list[str]
    pass_: bool
    first_hit_position: int | None
    returned_topk: list[dict[str, Any]]
    matched_expectations: dict[str, Any]
    notes: str


def db_connect(database_url: str) -> psycopg.Connection[Any]:
    return psycopg.connect(database_url)


def load_queries(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise SemanticEvalError("queries file precisa conter uma lista JSON")
    return raw


def candidate_texts(row: dict[str, Any]) -> list[str]:
    values = [
        row.get("element_id"),
        row.get("canonical_label"),
        row.get("canonical_ip"),
        row.get("canonical_hostname"),
        row.get("canonical_org"),
        row.get("role_hint_current"),
        row.get("element_kind"),
        row.get("ip_scope"),
        row.get("semantic_profile_text"),
    ]
    return [str(value).lower() for value in values if value is not None]


def row_matches_label_contains(row: dict[str, Any], label_parts: list[str]) -> bool:
    if not label_parts:
        return True
    texts = candidate_texts(row)
    for part in label_parts:
        needle = part.lower()
        if any(needle in text for text in texts):
            return True
    return False


def row_matches_category(row: dict[str, Any], categories: list[str]) -> bool:
    if not categories:
        return False
    for category in categories:
        predicate = CATEGORY_PREDICATES.get(category)
        if predicate and predicate(row):
            return True
    return False


def row_matches_element_ids(row: dict[str, Any], element_ids: list[str]) -> bool:
    if not element_ids:
        return False
    return row["element_id"] in element_ids


def first_hit_position(rows: list[dict[str, Any]], spec: dict[str, Any]) -> int | None:
    for index, row in enumerate(rows, start=1):
        if row_matches_element_ids(row, spec.get("expected_element_ids", [])):
            return index
        if row_matches_label_contains(row, spec.get("expected_label_contains", [])):
            return index
        if row_matches_category(row, spec.get("expected_categories", [])):
            return index
    return None


def evaluate_query(rows: list[dict[str, Any]], spec: dict[str, Any]) -> tuple[bool, int | None, dict[str, Any]]:
    mode = spec["expected_match_mode"]
    expected_element_ids = list(spec.get("expected_element_ids", []))
    expected_label_contains = list(spec.get("expected_label_contains", []))
    expected_categories = list(spec.get("expected_categories", []))

    matched = {
        "element_ids": [],
        "labels": [],
        "categories": [],
    }
    for row in rows:
        if row["element_id"] in expected_element_ids:
            matched["element_ids"].append(row["element_id"])
        if row_matches_label_contains(row, expected_label_contains):
            matched["labels"].append(row["element_id"])
        if row_matches_category(row, expected_categories):
            matched["categories"].append(row["element_id"])

    if mode == "top1_expected":
        top1 = rows[0] if rows else None
        passed = False
        if top1 is not None:
            passed = (
                row_matches_element_ids(top1, expected_element_ids)
                or row_matches_label_contains(top1, expected_label_contains)
                or row_matches_category(top1, expected_categories)
            )
        return passed, first_hit_position(rows, spec), matched

    if mode == "category_contains":
        passed = bool(matched["categories"])
        return passed, first_hit_position(rows, spec), matched

    if mode == "topk_contains":
        groups = []
        if expected_element_ids:
            groups.append(bool(matched["element_ids"]))
        if expected_label_contains:
            groups.append(bool(matched["labels"]))
        if expected_categories:
            groups.append(bool(matched["categories"]))
        passed = all(groups) if groups else False
        return passed, first_hit_position(rows, spec), matched

    raise SemanticEvalError(f"expected_match_mode inválido: {mode}")


def serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "element_id": row["element_id"],
        "canonical_label": row.get("canonical_label"),
        "canonical_ip": row.get("canonical_ip"),
        "canonical_hostname": row.get("canonical_hostname"),
        "canonical_org": row.get("canonical_org"),
        "role_hint_current": row.get("role_hint_current"),
        "element_kind": row.get("element_kind"),
        "ip_scope": row.get("ip_scope"),
        "score": row.get("score"),
        "distance": row.get("distance"),
    }


def render_markdown(summary: dict[str, Any], results: list[QueryResult], queries_file: str, limit: int) -> str:
    lines = [
        "# Avaliação semântica da Camada 1",
        "",
        f"- queries_file: `{queries_file}`",
        f"- limit: `{limit}`",
        f"- embedding_provider: `{summary['embedding_provider']}`",
        f"- embedding_model: `{summary['embedding_model']}`",
        f"- total_queries: `{summary['total_queries']}`",
        f"- total_pass: `{summary['total_pass']}`",
        f"- total_fail: `{summary['total_fail']}`",
        f"- hit_rate: `{summary['hit_rate']:.3f}`",
        f"- mean_first_hit_position: `{summary['mean_first_hit_position']}`",
        "",
        "## Por consulta",
        "",
        "| query_id | mode | pass | first_hit | top1 | topk |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for result in results:
        top1 = result.returned_topk[0]["element_id"] if result.returned_topk else "none"
        topk = ", ".join(row["element_id"] for row in result.returned_topk[:3]) or "none"
        lines.append(
            f"| {result.query_id} | {result.expected_match_mode} | {'pass' if result.pass_ else 'fail'} | "
            f"{result.first_hit_position or 'none'} | {top1} | {topk} |"
        )
    lines.extend(
        [
            "",
            "## Leitura",
            "",
            f"- acertos: `{summary['total_pass']}`",
            f"- falhas: `{summary['total_fail']}`",
            "- a avaliação usa `topomemory.network_element_semantic` e a busca semântica auxiliar atual",
            "- a identidade determinística não é alterada por este benchmark",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark mínimo da busca semântica da Camada 1.")
    parser.add_argument("--queries-file", default="schemas/semantic_eval_queries.json", help="arquivo JSON com a bateria de queries")
    parser.add_argument("--limit", type=int, default=5, help="top-k de retorno por query")
    parser.add_argument("--json-out", help="arquivo JSON de resultados")
    parser.add_argument("--markdown-out", help="arquivo Markdown de relatório")
    parser.add_argument("--fail-on-miss", action="store_true", help="retorna erro se alguma query falhar")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"), help="DSN do PostgreSQL")
    args = parser.parse_args()

    if not args.database_url:
        raise SemanticEvalError("DATABASE_URL não definido")
    try:
        provider = get_embedding_provider()
    except EmbeddingProviderError as exc:
        raise SemanticEvalError(str(exc)) from exc

    queries_path = Path(args.queries_file)
    queries = load_queries(queries_path)
    results: list[QueryResult] = []

    with db_connect(args.database_url) as conn:
        for spec in queries:
            query_vector = vector_literal(provider.embed_text(spec["query_text"]))
            rows = search_elements(
                conn,
                query=spec["query_text"],
                limit=args.limit,
                embedding_model=provider.model_name(),
                query_vector=query_vector,
            )
            passed, hit_position, matched = evaluate_query(rows, spec)
            results.append(
                QueryResult(
                    query_id=spec["query_id"],
                    query_text=spec["query_text"],
                    category=spec["category"],
                    expected_match_mode=spec["expected_match_mode"],
                    expected_element_ids=list(spec.get("expected_element_ids", [])),
                    expected_label_contains=list(spec.get("expected_label_contains", [])),
                    expected_categories=list(spec.get("expected_categories", [])),
                    pass_=passed,
                    first_hit_position=hit_position,
                    returned_topk=[serialize_row(row) for row in rows],
                    matched_expectations=matched,
                    notes=spec.get("notes", ""),
                )
            )

    total_queries = len(results)
    total_pass = sum(1 for result in results if result.pass_)
    total_fail = total_queries - total_pass
    hit_rate = total_pass / total_queries if total_queries else 0.0
    hit_positions = [result.first_hit_position for result in results if result.pass_ and result.first_hit_position is not None]
    mean_first_hit = mean(hit_positions) if hit_positions else None

    summary = {
        "queries_file": str(queries_path),
        "limit": args.limit,
        "embedding_provider": os.environ.get(EMBEDDING_PROVIDER_ENV, "hash"),
        "embedding_model": provider.model_name(),
        "total_queries": total_queries,
        "total_pass": total_pass,
        "total_fail": total_fail,
        "hit_rate": hit_rate,
        "mean_first_hit_position": mean_first_hit,
    }
    payload = {
        "summary": summary,
        "results": [
            {
                "query_id": result.query_id,
                "query_text": result.query_text,
                "category": result.category,
                "expected_match_mode": result.expected_match_mode,
                "expected_element_ids": result.expected_element_ids,
                "expected_label_contains": result.expected_label_contains,
                "expected_categories": result.expected_categories,
                "pass": result.pass_,
                "first_hit_position": result.first_hit_position,
                "returned_topk": result.returned_topk,
                "matched_expectations": result.matched_expectations,
                "notes": result.notes,
            }
            for result in results
        ],
    }

    report_md = render_markdown(summary, results, str(queries_path), args.limit)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    if args.markdown_out:
        Path(args.markdown_out).write_text(report_md, encoding="utf-8")

    print(
        json.dumps(
            {
                "summary": summary,
            },
            ensure_ascii=False,
            default=str,
        )
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    for result in results:
        print(
            json.dumps(
                {
                    "query_id": result.query_id,
                    "query_text": result.query_text,
                    "pass": result.pass_,
                    "first_hit_position": result.first_hit_position,
                    "top1": result.returned_topk[0]["element_id"] if result.returned_topk else None,
                    "topk": [row["element_id"] for row in result.returned_topk],
                },
                ensure_ascii=False,
                default=str,
            )
        )

    if args.fail_on_miss and total_fail:
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticEvalError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
