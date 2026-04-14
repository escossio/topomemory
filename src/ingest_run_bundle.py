#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.types.json import Jsonb


class IngestionError(Exception):
    pass


@dataclass(frozen=True)
class RunPayload:
    run_id: str
    collector_id: str
    target_type: str
    target_value: str
    service_hint: str
    scenario: str
    started_at: datetime
    finished_at: datetime
    run_status: str
    collection_health: str
    summary: str | None
    tags_json: list[Any]
    scenario_version: str | None
    notes: str | None


def load_json_file(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise IngestionError(f"não foi possível ler {path}: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise IngestionError(f"JSON inválido em {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise IngestionError(f"{path} deve conter um objeto JSON no nível raiz")

    return data


def require_mapping(data: dict[str, Any], key: str, source: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise IngestionError(f"{source} precisa conter um objeto '{key}'")
    return value


def require_list(data: dict[str, Any], key: str, source: str) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise IngestionError(f"{source} precisa conter uma lista '{key}'")
    return value


def require_text(data: dict[str, Any], key: str, source: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise IngestionError(f"{source} precisa conter o campo textual obrigatório '{key}'")
    return value


def optional_text(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise IngestionError(f"campo opcional '{key}' precisa ser texto quando presente")
    stripped = value.strip()
    return stripped or None


def parse_timestamp(value: str, field_name: str) -> datetime:
    candidate = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise IngestionError(f"timestamp inválido em '{field_name}': {value}") from exc
    if parsed.tzinfo is None:
        raise IngestionError(f"timestamp '{field_name}' precisa ter timezone explícito")
    return parsed


def join_notes(notes: Any) -> str | None:
    if notes is None:
        return None
    if isinstance(notes, str):
        stripped = notes.strip()
        return stripped or None
    if isinstance(notes, list):
        items = [str(item).strip() for item in notes if str(item).strip()]
        return "\n".join(items) if items else None
    raise IngestionError("campo notes precisa ser texto ou lista de textos")


def normalize_bundle_notes(bundle: dict[str, Any]) -> str | None:
    notes = bundle.get("notes")
    return join_notes(notes)


def normalize_run_notes(manifest: dict[str, Any]) -> str | None:
    return join_notes(manifest.get("notes"))


def derive_bundle_id(run_id: str, bundle: dict[str, Any]) -> str:
    bundle_id = bundle.get("bundle_id")
    if bundle_id is None:
        return f"bundle-{run_id}"
    if not isinstance(bundle_id, str) or not bundle_id.strip():
        raise IngestionError("bundle_id precisa ser texto não vazio quando presente")
    return bundle_id.strip()


def derive_bundle_version(bundle: dict[str, Any]) -> str:
    bundle_version = bundle.get("bundle_version")
    if bundle_version is None:
        return "layer0-v1"
    if not isinstance(bundle_version, str) or not bundle_version.strip():
        raise IngestionError("bundle_version precisa ser texto não vazio quando presente")
    return bundle_version.strip()


def validate_run_manifest(manifest: dict[str, Any]) -> RunPayload:
    run_id = require_text(manifest, "run_id", "run_manifest")
    collector_id = require_text(manifest, "collector_id", "run_manifest")
    target_type = require_text(manifest, "target_type", "run_manifest")
    target_value = require_text(manifest, "target_value", "run_manifest")
    service_hint = require_text(manifest, "service_hint", "run_manifest")
    scenario = require_text(manifest, "scenario", "run_manifest")
    started_at = parse_timestamp(require_text(manifest, "started_at", "run_manifest"), "started_at")
    finished_at = parse_timestamp(require_text(manifest, "finished_at", "run_manifest"), "finished_at")
    run_status = require_text(manifest, "run_status", "run_manifest")
    collection_health = require_text(manifest, "collection_health", "run_manifest")

    if finished_at < started_at:
        raise IngestionError("run_manifest.finished_at não pode ser anterior a started_at")

    if run_status not in {"success", "partial", "failed"}:
        raise IngestionError("run_manifest.run_status inválido")

    if collection_health not in {"healthy", "degraded", "blocked"}:
        raise IngestionError("run_manifest.collection_health inválido")

    summary = optional_text(manifest, "summary")
    scenario_version = optional_text(manifest, "scenario_version")
    notes = normalize_run_notes(manifest)

    tags_value = manifest.get("tags")
    if tags_value is None:
        tags_json: list[Any] = []
    elif isinstance(tags_value, list):
        tags_json = tags_value
    else:
        raise IngestionError("run_manifest.tags precisa ser uma lista quando presente")

    return RunPayload(
        run_id=run_id,
        collector_id=collector_id,
        target_type=target_type,
        target_value=target_value,
        service_hint=service_hint,
        scenario=scenario,
        started_at=started_at,
        finished_at=finished_at,
        run_status=run_status,
        collection_health=collection_health,
        summary=summary,
        tags_json=tags_json,
        scenario_version=scenario_version,
        notes=notes,
    )


def validate_bundle(bundle: dict[str, Any], expected_run_id: str, expected_collector_id: str) -> tuple[str, str]:
    run_context = require_mapping(bundle, "run_context", "ingestion_bundle")
    bundle_run_id = require_text(run_context, "run_id", "ingestion_bundle.run_context")
    bundle_collector_id = require_text(run_context, "collector_id", "ingestion_bundle.run_context")

    if bundle_run_id != expected_run_id:
        raise IngestionError(
            f"run_id divergente entre manifest ({expected_run_id}) e bundle.run_context ({bundle_run_id})"
        )

    if bundle_collector_id != expected_collector_id:
        raise IngestionError(
            f"collector_id divergente entre manifest ({expected_collector_id}) e bundle.run_context ({bundle_collector_id})"
        )

    for key in (
        "target_type",
        "target_value",
        "service_hint",
        "scenario",
        "started_at",
        "finished_at",
        "run_status",
        "collection_health",
    ):
        require_text(run_context, key, "ingestion_bundle.run_context")

    require_list(bundle, "observed_elements", "ingestion_bundle")
    require_list(bundle, "observed_relations", "ingestion_bundle")
    require_list(bundle, "artifacts_manifest", "ingestion_bundle")

    confidence = require_mapping(bundle, "ingestion_confidence", "ingestion_bundle")
    confidence_level = require_text(confidence, "level", "ingestion_bundle.ingestion_confidence")
    if confidence_level not in {"minimal", "complete", "rejected"}:
        raise IngestionError("ingestion_bundle.ingestion_confidence.level inválido")

    bundle_id = derive_bundle_id(expected_run_id, bundle)
    bundle_version = derive_bundle_version(bundle)

    return bundle_id, bundle_version


def validate_bundle_run_context_matches_manifest(bundle: dict[str, Any], manifest: dict[str, Any]) -> None:
    run_context = bundle["run_context"]
    for key in (
        "run_id",
        "collector_id",
        "target_type",
        "target_value",
        "service_hint",
        "scenario",
        "started_at",
        "finished_at",
        "run_status",
        "collection_health",
    ):
        if run_context.get(key) != manifest.get(key):
            raise IngestionError(f"campo divergente entre manifest e bundle.run_context: {key}")


def infer_artifact_format(artifact: dict[str, Any]) -> str:
    mime_type = artifact.get("mime_type")
    if isinstance(mime_type, str) and mime_type.strip():
        return mime_type.strip()

    kind = artifact.get("kind")
    if kind == "manifest":
        return "application/json"
    if kind == "html_snapshot":
        return "text/html"
    if kind in {"network_log", "json_log"}:
        return "application/json"
    return "application/octet-stream"


def infer_artifact_notes(artifact: dict[str, Any]) -> str | None:
    parts: list[str] = []
    purpose = artifact.get("purpose")
    if isinstance(purpose, str) and purpose.strip():
        parts.append(f"purpose={purpose.strip()}")
    sha256 = artifact.get("sha256")
    if isinstance(sha256, str) and sha256.strip():
        parts.append(f"sha256={sha256.strip()}")
    return "; ".join(parts) if parts else None


def infer_artifact_generated_at(artifact: dict[str, Any], fallback: datetime) -> datetime:
    generated_at = artifact.get("generated_at")
    if generated_at is None:
        return fallback
    if not isinstance(generated_at, str) or not generated_at.strip():
        raise IngestionError("generated_at do artefato precisa ser texto quando presente")
    return parse_timestamp(generated_at.strip(), "artifacts[].generated_at")


def infer_artifact_status(artifact: dict[str, Any]) -> str:
    status = artifact.get("artifact_status")
    if status is None:
        status = artifact.get("status")
    if status is None:
        return "present"
    if not isinstance(status, str) or status.strip() not in {"present", "missing", "failed", "skipped"}:
        raise IngestionError("artifact_status do artefato inválido quando presente")
    return status.strip()


def ensure_unique_artifact_ids(artifacts: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for artifact in artifacts:
        artifact_id = require_text(artifact, "artifact_id", "run_manifest.artifacts[]")
        if artifact_id in seen:
            duplicates.add(artifact_id)
        seen.add(artifact_id)
    if duplicates:
        joined = ", ".join(sorted(duplicates))
        raise IngestionError(f"artifact_id duplicado no run_manifest.artifacts: {joined}")


def require_collector_exists(conn: psycopg.Connection[Any], collector_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM topomemory.collector WHERE collector_id = %s",
            (collector_id,),
        )
        if cur.fetchone() is None:
            raise IngestionError(f"collector_id não encontrado na base: {collector_id}")


def upsert_run(conn: psycopg.Connection[Any], payload: RunPayload) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO topomemory.run (
              run_id,
              collector_id,
              target_type,
              target_value,
              service_hint,
              scenario,
              started_at,
              finished_at,
              run_status,
              collection_health,
              summary,
              tags_json,
              scenario_version,
              notes
            )
            VALUES (
              %(run_id)s,
              %(collector_id)s,
              %(target_type)s,
              %(target_value)s,
              %(service_hint)s,
              %(scenario)s,
              %(started_at)s,
              %(finished_at)s,
              %(run_status)s,
              %(collection_health)s,
              %(summary)s,
              %(tags_json)s,
              %(scenario_version)s,
              %(notes)s
            )
            ON CONFLICT (run_id) DO UPDATE SET
              collector_id = EXCLUDED.collector_id,
              target_type = EXCLUDED.target_type,
              target_value = EXCLUDED.target_value,
              service_hint = EXCLUDED.service_hint,
              scenario = EXCLUDED.scenario,
              started_at = EXCLUDED.started_at,
              finished_at = EXCLUDED.finished_at,
              run_status = EXCLUDED.run_status,
              collection_health = EXCLUDED.collection_health,
              summary = EXCLUDED.summary,
              tags_json = EXCLUDED.tags_json,
              scenario_version = EXCLUDED.scenario_version,
              notes = EXCLUDED.notes
            """,
            {
                "run_id": payload.run_id,
                "collector_id": payload.collector_id,
                "target_type": payload.target_type,
                "target_value": payload.target_value,
                "service_hint": payload.service_hint,
                "scenario": payload.scenario,
                "started_at": payload.started_at,
                "finished_at": payload.finished_at,
                "run_status": payload.run_status,
                "collection_health": payload.collection_health,
                "summary": payload.summary,
                "tags_json": Jsonb(payload.tags_json),
                "scenario_version": payload.scenario_version,
                "notes": payload.notes,
            },
        )


def replace_run_artifacts(
    conn: psycopg.Connection[Any],
    run_id: str,
    artifacts: list[dict[str, Any]],
    fallback_generated_at: datetime,
) -> None:
    ensure_unique_artifact_ids(artifacts)
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM topomemory.run_artifact WHERE run_id = %s",
            (run_id,),
        )

        for artifact in artifacts:
            artifact_id = require_text(artifact, "artifact_id", "run_manifest.artifacts[]")
            artifact_type = require_text(artifact, "kind", "run_manifest.artifacts[]")
            artifact_path = require_text(artifact, "path", "run_manifest.artifacts[]")
            artifact_status = infer_artifact_status(artifact)
            artifact_format = infer_artifact_format(artifact)
            generated_at = infer_artifact_generated_at(artifact, fallback_generated_at)
            notes = infer_artifact_notes(artifact)

            cur.execute(
                """
                INSERT INTO topomemory.run_artifact (
                  artifact_id,
                  run_id,
                  artifact_type,
                  artifact_path,
                  artifact_status,
                  artifact_format,
                  generated_at,
                  notes
                )
                VALUES (
                  %(artifact_id)s,
                  %(run_id)s,
                  %(artifact_type)s,
                  %(artifact_path)s,
                  %(artifact_status)s,
                  %(artifact_format)s,
                  %(generated_at)s,
                  %(notes)s
                )
                ON CONFLICT (artifact_id) DO UPDATE SET
                  run_id = EXCLUDED.run_id,
                  artifact_type = EXCLUDED.artifact_type,
                  artifact_path = EXCLUDED.artifact_path,
                  artifact_status = EXCLUDED.artifact_status,
                  artifact_format = EXCLUDED.artifact_format,
                  generated_at = EXCLUDED.generated_at,
                  notes = EXCLUDED.notes
                """,
                {
                    "artifact_id": artifact_id,
                    "run_id": run_id,
                    "artifact_type": artifact_type,
                    "artifact_path": artifact_path,
                    "artifact_status": artifact_status,
                    "artifact_format": artifact_format,
                    "generated_at": generated_at,
                    "notes": notes,
                },
            )


def upsert_ingestion_bundle(
    conn: psycopg.Connection[Any],
    bundle: dict[str, Any],
    run_id: str,
    bundle_id: str,
    bundle_version: str,
) -> None:
    confidence = require_mapping(bundle, "ingestion_confidence", "ingestion_bundle")
    run_context = bundle["run_context"]
    observed_elements = bundle["observed_elements"]
    observed_relations = bundle["observed_relations"]
    artifacts_manifest = bundle["artifacts_manifest"]

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO topomemory.ingestion_bundle (
              bundle_id,
              run_id,
              bundle_version,
              ingestion_confidence,
              run_context_json,
              observed_elements_json,
              observed_relations_json,
              artifacts_manifest_json,
              notes
            )
            VALUES (
              %(bundle_id)s,
              %(run_id)s,
              %(bundle_version)s,
              %(ingestion_confidence)s,
              %(run_context_json)s,
              %(observed_elements_json)s,
              %(observed_relations_json)s,
              %(artifacts_manifest_json)s,
              %(notes)s
            )
            ON CONFLICT (run_id) DO UPDATE SET
              bundle_id = EXCLUDED.bundle_id,
              bundle_version = EXCLUDED.bundle_version,
              ingestion_confidence = EXCLUDED.ingestion_confidence,
              run_context_json = EXCLUDED.run_context_json,
              observed_elements_json = EXCLUDED.observed_elements_json,
              observed_relations_json = EXCLUDED.observed_relations_json,
              artifacts_manifest_json = EXCLUDED.artifacts_manifest_json,
              notes = EXCLUDED.notes
            """,
            {
                "bundle_id": bundle_id,
                "run_id": run_id,
                "bundle_version": bundle_version,
                "ingestion_confidence": confidence["level"].strip(),
                "run_context_json": Jsonb(run_context),
                "observed_elements_json": Jsonb(observed_elements),
                "observed_relations_json": Jsonb(observed_relations),
                "artifacts_manifest_json": Jsonb(artifacts_manifest),
                "notes": normalize_bundle_notes(bundle),
            },
        )


def fetch_counts(conn: psycopg.Connection[Any], run_id: str) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              (SELECT count(*) FROM topomemory.run WHERE run_id = %s),
              (SELECT count(*) FROM topomemory.run_artifact WHERE run_id = %s),
              (SELECT count(*) FROM topomemory.ingestion_bundle WHERE run_id = %s)
            """,
            (run_id, run_id, run_id),
        )
        run_count, artifact_count, bundle_count = cur.fetchone()
        return {
            "run": int(run_count),
            "run_artifact": int(artifact_count),
            "ingestion_bundle": int(bundle_count),
        }


def ingest(manifest_path: Path, bundle_path: Path) -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise IngestionError("variável de ambiente DATABASE_URL não definida")

    manifest = load_json_file(manifest_path)
    bundle = load_json_file(bundle_path)

    payload = validate_run_manifest(manifest)
    validate_bundle_run_context_matches_manifest(bundle, manifest)
    bundle_id, bundle_version = validate_bundle(bundle, payload.run_id, payload.collector_id)

    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            require_collector_exists(conn, payload.collector_id)
            upsert_run(conn, payload)
            replace_run_artifacts(
                conn,
                payload.run_id,
                require_list(manifest, "artifacts", "run_manifest"),
                payload.finished_at,
            )
            upsert_ingestion_bundle(conn, bundle, payload.run_id, bundle_id, bundle_version)

        counts = fetch_counts(conn, payload.run_id)

    print(
        "ingestão concluída: "
        f"run={payload.run_id} "
        f"collector={payload.collector_id} "
        f"artifacts={counts['run_artifact']} "
        f"bundle={bundle_id} "
        f"bundle_version={bundle_version}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingere um run_manifest e um ingestion_bundle na Camada 0 do topomemory.",
    )
    parser.add_argument("manifest_json", type=Path, help="caminho para run_manifest.example.json ou equivalente")
    parser.add_argument("bundle_json", type=Path, help="caminho para ingestion_bundle.example.json ou equivalente")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        ingest(args.manifest_json, args.bundle_json)
        return 0
    except IngestionError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - proteção de borda
        print(f"erro inesperado: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
