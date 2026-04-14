#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import psycopg

from embedding_provider import EMBEDDING_PROVIDER_ENV, EmbeddingProviderError, get_embedding_provider, vector_literal
from semantic_support import SEMANTIC_PROFILE_VERSION, get_semantic_profile_variant


class SemanticEmbeddingError(RuntimeError):
    pass


def db_connect(database_url: str) -> psycopg.Connection[Any]:
    return psycopg.connect(database_url)


def load_pending_profiles(conn: psycopg.Connection[Any], *, embedding_model: str) -> list[dict[str, Any]]:
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
            (embedding_model, SEMANTIC_PROFILE_VERSION),
        )
        rows = cur.fetchall()

    columns = ["semantic_id", "element_id", "semantic_profile_text"]
    return [dict(zip(columns, row, strict=True)) for row in rows]


def persist_embedding(conn: psycopg.Connection[Any], *, element_id: str, vector_text: str, embedding_model: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE topomemory.network_element_semantic
            SET embedding_vector = %s::vector,
                embedding_model = %s,
                embedding_created_at = now()
            WHERE element_id = %s
            """,
            (vector_text, embedding_model, element_id),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera e persiste embeddings determinísticos para network_element_semantic.")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"), help="DSN do PostgreSQL")
    args = parser.parse_args()

    if not args.database_url:
        raise SemanticEmbeddingError("DATABASE_URL não definido")

    try:
        provider = get_embedding_provider()
    except EmbeddingProviderError as exc:
        raise SemanticEmbeddingError(str(exc)) from exc

    with db_connect(args.database_url) as conn:
        with conn.transaction():
            rows = load_pending_profiles(conn, embedding_model=provider.model_name())
            texts = [row["semantic_profile_text"] for row in rows]
            embeddings = provider.embed_batch(texts)
            for row, embedding in zip(rows, embeddings, strict=True):
                persist_embedding(
                    conn,
                    element_id=row["element_id"],
                    vector_text=vector_literal(embedding),
                    embedding_model=provider.model_name(),
                )

    print(
        json.dumps(
            {
                "status": "ok",
                "semantic_profile_version": SEMANTIC_PROFILE_VERSION,
                "profile_variant": get_semantic_profile_variant(),
                "embedding_provider": os.environ.get(EMBEDDING_PROVIDER_ENV, "hash"),
                "embedding_model": provider.model_name(),
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
