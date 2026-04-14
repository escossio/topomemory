#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import psycopg

from embedding_provider import EmbeddingProviderError, get_embedding_provider
from semantic_support import SEMANTIC_PROFILE_VERSION, build_semantic_profile_text, get_semantic_profile_variant


class SemanticProfileError(RuntimeError):
    pass


def db_connect(database_url: str) -> psycopg.Connection[Any]:
    return psycopg.connect(database_url)


def load_network_element_rows(conn: psycopg.Connection[Any]) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH resolved AS (
              SELECT
                COALESCE(matched_element_id, new_element_id) AS element_id,
                decision_type,
                run_id,
                observed_element_id
              FROM topomemory.identity_decision
              WHERE COALESCE(matched_element_id, new_element_id) IS NOT NULL
            )
            SELECT
              ne.element_id,
              ne.canonical_label,
              ne.element_kind,
              ne.ip_scope,
              ne.canonical_ip,
              ne.canonical_hostname,
              ne.canonical_asn,
              ne.canonical_org,
              ne.confidence_current,
              ne.role_hint_current,
              ne.first_seen_at,
              ne.last_seen_at,
              COALESCE(stats.decision_count, 0) AS decision_count,
              COALESCE(stats.matched_count, 0) AS matched_count,
              COALESCE(stats.new_count, 0) AS new_count,
              COALESCE(stats.skipped_count, 0) AS skipped_count,
              COALESCE(stats.run_count, 0) AS run_count,
              COALESCE(stats.source_types, '') AS source_types,
              COALESCE(stats.observed_ip_scopes, '') AS observed_ip_scopes,
              COALESCE(stats.service_contexts, '') AS service_contexts
            FROM topomemory.network_element ne
            LEFT JOIN LATERAL (
              SELECT
                COUNT(*) AS decision_count,
                COUNT(*) FILTER (WHERE resolved.decision_type = 'matched_existing_entity') AS matched_count,
                COUNT(*) FILTER (WHERE resolved.decision_type = 'new_entity_created') AS new_count,
                COUNT(*) FILTER (WHERE resolved.decision_type LIKE 'skipped_%') AS skipped_count,
                COUNT(DISTINCT resolved.run_id) AS run_count,
                STRING_AGG(DISTINCT oe.source_type, ', ' ORDER BY oe.source_type) AS source_types,
                STRING_AGG(DISTINCT oe.ip_scope, ', ' ORDER BY oe.ip_scope) AS observed_ip_scopes,
                STRING_AGG(DISTINCT oe.service_context, ', ' ORDER BY oe.service_context) AS service_contexts
              FROM resolved
              JOIN topomemory.observed_element oe
                ON oe.observed_element_id = resolved.observed_element_id
              WHERE resolved.element_id = ne.element_id
            ) stats ON true
            ORDER BY ne.element_id
            """
        )
        rows = cur.fetchall()

    columns = [
        "element_id",
        "canonical_label",
        "element_kind",
        "ip_scope",
        "canonical_ip",
        "canonical_hostname",
        "canonical_asn",
        "canonical_org",
        "confidence_current",
        "role_hint_current",
        "first_seen_at",
        "last_seen_at",
        "decision_count",
        "matched_count",
        "new_count",
        "skipped_count",
        "run_count",
        "source_types",
        "observed_ip_scopes",
        "service_contexts",
    ]
    return [dict(zip(columns, row, strict=True)) for row in rows]


def upsert_semantic_profile(conn: psycopg.Connection[Any], row: dict[str, Any], *, variant: str) -> None:
    semantic_profile_text = build_semantic_profile_text(row, variant=variant)
    payload = {
        "semantic_id": f"semantic-{row['element_id']}",
        "element_id": row["element_id"],
        "semantic_profile_text": semantic_profile_text,
        "semantic_profile_version": SEMANTIC_PROFILE_VERSION,
        "embedding_model": "openai",
    }
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO topomemory.network_element_semantic (
              semantic_id,
              element_id,
              semantic_profile_text,
              semantic_profile_version,
              embedding_model,
              embedding_vector,
              embedding_created_at
            )
            VALUES (
              %(semantic_id)s,
              %(element_id)s,
              %(semantic_profile_text)s,
              %(semantic_profile_version)s,
              %(embedding_model)s,
              NULL,
              NULL
            )
            ON CONFLICT (element_id) DO UPDATE SET
              semantic_id = EXCLUDED.semantic_id,
              semantic_profile_text = EXCLUDED.semantic_profile_text,
              semantic_profile_version = EXCLUDED.semantic_profile_version,
              embedding_model = EXCLUDED.embedding_model,
              embedding_vector = CASE
                WHEN topomemory.network_element_semantic.semantic_profile_text IS DISTINCT FROM EXCLUDED.semantic_profile_text
                  OR topomemory.network_element_semantic.semantic_profile_version IS DISTINCT FROM EXCLUDED.semantic_profile_version
                  OR topomemory.network_element_semantic.embedding_model IS DISTINCT FROM EXCLUDED.embedding_model
                THEN NULL
                ELSE topomemory.network_element_semantic.embedding_vector
              END,
              embedding_created_at = CASE
                WHEN topomemory.network_element_semantic.semantic_profile_text IS DISTINCT FROM EXCLUDED.semantic_profile_text
                  OR topomemory.network_element_semantic.semantic_profile_version IS DISTINCT FROM EXCLUDED.semantic_profile_version
                  OR topomemory.network_element_semantic.embedding_model IS DISTINCT FROM EXCLUDED.embedding_model
                THEN NULL
                ELSE topomemory.network_element_semantic.embedding_created_at
              END,
              updated_at = now()
            """,
            payload,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Constrói os perfis semânticos determinísticos de network_element.")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"), help="DSN do PostgreSQL")
    args = parser.parse_args()

    if not args.database_url:
        raise SemanticProfileError("DATABASE_URL não definido")
    variant = get_semantic_profile_variant()
    try:
        embedding_model = get_embedding_provider().model_name()
    except EmbeddingProviderError as exc:
        raise SemanticProfileError(str(exc)) from exc

    with db_connect(args.database_url) as conn:
        with conn.transaction():
            rows = load_network_element_rows(conn)
            for row in rows:
                upsert_semantic_profile(conn, row, variant=variant)

    print(
        json.dumps(
            {
                "status": "ok",
                "semantic_profile_version": SEMANTIC_PROFILE_VERSION,
                "profile_variant": variant,
                "embedding_model": embedding_model,
                "indexed_elements": len(rows),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticProfileError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
