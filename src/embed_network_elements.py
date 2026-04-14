#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import psycopg

from semantic_support import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL, SEMANTIC_PROFILE_VERSION, embed_text, vector_literal


class SemanticEmbeddingError(RuntimeError):
    pass


def db_connect(database_url: str) -> psycopg.Connection[Any]:
    return psycopg.connect(database_url)


def load_pending_profiles(conn: psycopg.Connection[Any]) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT semantic_id, element_id, semantic_profile_text
            FROM topomemory.network_element_semantic
            WHERE embedding_vector IS NULL
               OR embedding_created_at IS NULL
               OR embedding_model <> %s
               OR semantic_profile_version <> %s
            ORDER BY element_id
            """,
            (EMBEDDING_MODEL, SEMANTIC_PROFILE_VERSION),
        )
        rows = cur.fetchall()

    columns = ["semantic_id", "element_id", "semantic_profile_text"]
    return [dict(zip(columns, row, strict=True)) for row in rows]


def persist_embedding(conn: psycopg.Connection[Any], *, element_id: str, vector_text: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            UPDATE topomemory.network_element_semantic
            SET embedding_vector = %s::vector,
                embedding_model = %s,
                embedding_created_at = now()
            WHERE element_id = %s
            """,
            (vector_text, EMBEDDING_MODEL, element_id),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera e persiste embeddings determinísticos para network_element_semantic.")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"), help="DSN do PostgreSQL")
    args = parser.parse_args()

    if not args.database_url:
        raise SemanticEmbeddingError("DATABASE_URL não definido")

    with db_connect(args.database_url) as conn:
        with conn.transaction():
            rows = load_pending_profiles(conn)
            for row in rows:
                embedding = embed_text(row["semantic_profile_text"])
                persist_embedding(conn, element_id=row["element_id"], vector_text=vector_literal(embedding))

    print(
        json.dumps(
            {
                "status": "ok",
                "semantic_profile_version": SEMANTIC_PROFILE_VERSION,
                "embedding_model": EMBEDDING_MODEL,
                "embedded_elements": len(rows),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticEmbeddingError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
