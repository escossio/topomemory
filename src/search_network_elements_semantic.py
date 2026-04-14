#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import psycopg

from semantic_support import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL, embed_text, vector_literal


class SemanticSearchError(RuntimeError):
    pass


def db_connect(database_url: str) -> psycopg.Connection[Any]:
    return psycopg.connect(database_url)


def search_elements(conn: psycopg.Connection[Any], *, query: str, limit: int) -> list[dict[str, Any]]:
    query_vector = vector_literal(embed_text(query))
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT
              ne.element_id,
              ne.canonical_ip,
              ne.canonical_hostname,
              ne.canonical_org,
              ne.role_hint_current,
              nes.semantic_profile_text,
              1 - (nes.embedding_vector <=> %s::vector) AS score,
              (nes.embedding_vector <=> %s::vector) AS distance
            FROM topomemory.network_element_semantic nes
            JOIN topomemory.network_element ne
              ON ne.element_id = nes.element_id
            WHERE nes.embedding_vector IS NOT NULL
            ORDER BY nes.embedding_vector <=> %s::vector, ne.element_id
            LIMIT %s
            """,
            (query_vector, query_vector, query_vector, limit),
        )
        rows = cur.fetchall()

    columns = [
        "element_id",
        "canonical_ip",
        "canonical_hostname",
        "canonical_org",
        "role_hint_current",
        "semantic_profile_text",
        "score",
        "distance",
    ]
    return [dict(zip(columns, row, strict=True)) for row in rows]


def print_results(results: list[dict[str, Any]], *, show_profile: bool) -> None:
    for row in results:
        print(f"element_id={row['element_id']}")
        print(f"canonical_ip={row['canonical_ip'] or 'none'}")
        print(f"canonical_hostname={row['canonical_hostname'] or 'none'}")
        print(f"canonical_org={row['canonical_org'] or 'none'}")
        print(f"role_hint_current={row['role_hint_current'] or 'none'}")
        print(f"score={row['score']:.6f}")
        print(f"distance={row['distance']:.6f}")
        if show_profile:
            print("semantic_profile_text=")
            print(row["semantic_profile_text"].rstrip("\n"))
        else:
            snippet = row["semantic_profile_text"].replace("\n", " ")
            print(f"semantic_profile_snippet={snippet[:220]}")
        print("")


def main() -> int:
    parser = argparse.ArgumentParser(description="Busca semântica auxiliar sobre network_element.")
    parser.add_argument("query", help="texto da consulta")
    parser.add_argument("--limit", type=int, default=5, help="quantidade máxima de resultados")
    parser.add_argument("--show-profile", action="store_true", help="exibe o perfil semântico completo")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"), help="DSN do PostgreSQL")
    args = parser.parse_args()

    if not args.database_url:
        raise SemanticSearchError("DATABASE_URL não definido")
    if not args.query.strip():
        raise SemanticSearchError("consulta vazia")
    if args.limit < 1:
        raise SemanticSearchError("--limit precisa ser >= 1")

    with db_connect(args.database_url) as conn:
        results = search_elements(conn, query=args.query.strip(), limit=args.limit)

    print(
        json.dumps(
            {
                "query": args.query.strip(),
                "embedding_model": EMBEDDING_MODEL,
                "dimensions": EMBEDDING_DIMENSIONS,
                "result_count": len(results),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print_results(results, show_profile=args.show_profile)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticSearchError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
