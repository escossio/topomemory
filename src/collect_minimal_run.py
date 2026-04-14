#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COLLECTOR_ID = "vm-10.45.0.4"
DEFAULT_SCENARIO = "home_page"
DEFAULT_TARGET_TYPE = "domain"
DEFAULT_SERVICE_HINT = "public_home_page"
DEFAULT_BUNDLE_VERSION = "layer0-v1"


class CollectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class CommandResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str
    started_at: datetime
    finished_at: datetime


def now_local() -> datetime:
    return datetime.now().astimezone()


def slugify_target(target: str) -> str:
    cleaned = target.strip().lower()
    cleaned = re.sub(r"^https?://", "", cleaned)
    cleaned = re.sub(r"[^a-z0-9]+", "-", cleaned)
    cleaned = cleaned.strip("-")
    return cleaned or "target"


def timestamp_token(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%S%z")


def run_id_for(target: str, started_at: datetime) -> str:
    digest = hashlib.sha256(f"{target}|{started_at.isoformat()}".encode("utf-8")).hexdigest()[:8]
    return f"run-{timestamp_token(started_at)}-{slugify_target(target)}-{digest}"


def bundle_id_for(run_id: str) -> str:
    return f"bundle-{run_id}"


def json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def text_dump(path: Path, content: str) -> None:
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(args: list[str], output_path: Path, timeout: int = 60) -> CommandResult:
    started_at = now_local()
    proc = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ, "LC_ALL": "C", "LANG": "C"},
        cwd=str(REPO_ROOT),
    )
    finished_at = now_local()
    content = [
        f"command: {shlex.join(args)}",
        f"started_at: {started_at.isoformat()}",
        f"finished_at: {finished_at.isoformat()}",
        f"returncode: {proc.returncode}",
        "",
        "--- STDOUT ---",
        proc.stdout.rstrip("\n"),
        "",
        "--- STDERR ---",
        proc.stderr.rstrip("\n"),
        "",
    ]
    text_dump(output_path, "\n".join(content).rstrip("\n"))
    return CommandResult(
        args=args,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        started_at=started_at,
        finished_at=finished_at,
    )


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def unique_preserve_order(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def parse_dig_output(output: str, family: str) -> list[str]:
    records: list[str] = []
    for line in output.splitlines():
        candidate = line.strip()
        if family == "A" and re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", candidate):
            records.append(candidate)
        if family == "AAAA" and ":" in candidate:
            records.append(candidate)
    return records


def parse_host_output(output: str, family: str) -> list[str]:
    records: list[str] = []
    for line in output.splitlines():
        if family == "A":
            match = re.search(r"has address ([0-9.]+)$", line.strip())
        else:
            match = re.search(r"has IPv6 address ([0-9A-Fa-f:]+)$", line.strip())
        if match:
            records.append(match.group(1))
    return records


def parse_getent_output(output: str, family: str) -> list[str]:
    records: list[str] = []
    for line in output.splitlines():
        candidate = line.strip().split()
        if not candidate:
            continue
        address = candidate[0]
        if family == "A" and re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", address):
            records.append(address)
        if family == "AAAA" and ":" in address:
            records.append(address)
    return records


def resolve_dns(target: str, run_dir: Path) -> tuple[CommandResult, list[str], str]:
    dns_path = run_dir / "dns.txt"
    if command_exists("dig"):
        dns_tool = "dig"
        result = run_command(["dig", "+short", target, "A"], dns_path)
        v6_result = run_command(["dig", "+short", target, "AAAA"], run_dir / "dns_aaaa.txt")
        ipv4s = parse_dig_output(result.stdout, "A")
        ipv6s = parse_dig_output(v6_result.stdout, "AAAA")
    elif command_exists("host"):
        dns_tool = "host"
        result = run_command(["host", target], dns_path)
        v6_result = run_command(["host", "-t", "AAAA", target], run_dir / "dns_aaaa.txt")
        ipv4s = parse_host_output(result.stdout, "A")
        ipv6s = parse_host_output(v6_result.stdout, "AAAA")
    elif command_exists("getent"):
        dns_tool = "getent"
        result = run_command(["getent", "ahostsv4", target], dns_path)
        v6_result = run_command(["getent", "ahostsv6", target], run_dir / "dns_aaaa.txt")
        ipv4s = parse_getent_output(result.stdout, "A")
        ipv6s = parse_getent_output(v6_result.stdout, "AAAA")
    else:
        raise CollectionError("nenhuma ferramenta de DNS disponivel (dig, host ou getent)")

    dns_combined = [
        f"target: {target}",
        f"dns_tool: {dns_tool}",
        f"dns_a_returncode: {result.returncode}",
        f"dns_aaaa_returncode: {v6_result.returncode}",
        "",
        "--- A RECORDS ---",
        result.stdout.rstrip("\n"),
        "",
        "--- AAAA RECORDS ---",
        v6_result.stdout.rstrip("\n"),
        "",
    ]
    text_dump(dns_path, "\n".join(dns_combined).rstrip("\n"))
    (run_dir / "dns_aaaa.txt").unlink(missing_ok=True)
    return result, unique_preserve_order(ipv4s + ipv6s), dns_tool


def parse_traceroute_hops(output: str) -> list[dict[str, Any]]:
    hops: list[dict[str, Any]] = []
    for line in output.splitlines():
        match = re.match(r"^\s*(\d+)\s+([0-9A-Fa-f:.]+|\*)", line)
        if not match:
            continue
        hop_number = int(match.group(1))
        hop_value = match.group(2)
        if hop_value == "*":
            continue
        hops.append(
            {
                "hop_number": hop_number,
                "address": hop_value,
                "label": f"hop {hop_number}",
            }
        )
    return hops


def trace_route(target: str, run_dir: Path) -> tuple[CommandResult, list[dict[str, Any]], str]:
    trace_path = run_dir / "traceroute.txt"
    result = run_command(
        ["traceroute", "-n", "-m", "8", "-q", "1", "-w", "1", target],
        trace_path,
        timeout=120,
    )
    hops = parse_traceroute_hops(result.stdout)

    if hops:
        return result, hops, "traceroute.txt"

    mtr_path = run_dir / "mtr.txt"
    mtr_result = run_command(["mtr", "-r", "-n", "-c", "3", target], mtr_path, timeout=180)
    hops = []
    for line in mtr_result.stdout.splitlines():
        match = re.match(r"^\s*(\d+)\.\|\-\-\s+([0-9A-Fa-f:.]+)", line)
        if match:
            hops.append(
                {
                    "hop_number": int(match.group(1)),
                    "address": match.group(2),
                    "label": f"hop {match.group(1)}",
                }
            )

    return mtr_result, hops, "mtr.txt"


def fetch_http(target_url: str, run_dir: Path) -> CommandResult:
    http_path = run_dir / "http.txt"
    return run_command(
        [
            "curl",
            "-sS",
            "-L",
            "--head",
            "--connect-timeout",
            "10",
            "--max-time",
            "20",
            "--write-out",
            "\nFINAL_URL=%{url_effective}\nHTTP_CODE=%{http_code}\nREMOTE_IP=%{remote_ip}\nNUM_REDIRECTS=%{num_redirects}\n",
            target_url,
        ],
        http_path,
        timeout=90,
    )


def make_artifact(
    run_id: str,
    kind: str,
    path: Path,
    purpose: str,
    generated_at: datetime,
    mime_type: str,
    sha256: str | None = None,
) -> dict[str, Any]:
    rel_path = path.relative_to(REPO_ROOT).as_posix()
    artifact_id = f"{run_id}-{kind.replace('/', '-')}"
    return {
        "artifact_id": artifact_id,
        "kind": kind,
        "path": rel_path,
        "purpose": purpose,
        "generated_at": generated_at.isoformat(),
        "artifact_status": "present",
        **({"sha256": sha256} if sha256 is not None else {}),
        "mime_type": mime_type,
    }


def build_observations(
    run_id: str,
    target: str,
    dns_ips: list[str],
    hops: list[dict[str, Any]],
    evidence_paths: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    target_element_id = f"{slugify_target(target)}-target"
    observed_elements: list[dict[str, Any]] = [
        {
            "observation_id": f"{run_id}-obs-target",
            "element_id": target_element_id,
            "element_type": "target",
            "label": target,
            "evidence_ref": evidence_paths["http"],
            "confidence": 1.0,
        }
    ]
    observed_relations: list[dict[str, Any]] = []

    for index, ip in enumerate(dns_ips, start=1):
        element_id = f"{slugify_target(target)}-resolved-{index}"
        observed_elements.append(
            {
                "observation_id": f"{run_id}-obs-dns-{index}",
                "element_id": element_id,
                "element_type": "resolved_address",
                "label": ip,
                "evidence_ref": evidence_paths["dns"],
                "confidence": 0.98,
            }
        )
        observed_relations.append(
            {
                "relation_id": f"{run_id}-rel-dns-{index}",
                "from_element_id": target_element_id,
                "to_element_id": element_id,
                "relation_type": "resolves_to",
                "evidence_ref": evidence_paths["dns"],
                "confidence": 0.97,
            }
        )

    previous_hop_id: str | None = None
    for hop in hops:
        hop_number = int(hop["hop_number"])
        hop_address = str(hop["address"])
        hop_element_id = f"{slugify_target(target)}-hop-{hop_number:02d}"
        observed_elements.append(
            {
                "observation_id": f"{run_id}-obs-hop-{hop_number:02d}",
                "element_id": hop_element_id,
                "element_type": "network_hop",
                "label": f"hop {hop_number}: {hop_address}",
                "evidence_ref": evidence_paths["trace"],
                "confidence": 0.9,
            }
        )
        if previous_hop_id is not None:
            observed_relations.append(
                {
                    "relation_id": f"{run_id}-rel-hop-{hop_number - 1:02d}-{hop_number:02d}",
                    "from_element_id": previous_hop_id,
                    "to_element_id": hop_element_id,
                    "relation_type": "precedes",
                    "evidence_ref": evidence_paths["trace"],
                    "confidence": 0.88,
                }
            )
        previous_hop_id = hop_element_id

    return observed_elements, observed_relations


def build_summary(
    target: str,
    collector_id: str,
    dns_ips: list[str],
    hops: list[dict[str, Any]],
    http_result: CommandResult,
) -> str:
    http_code = "unknown"
    final_url = "unknown"
    remote_ip = "unknown"
    num_redirects = "unknown"
    for line in http_result.stdout.splitlines():
        if line.startswith("HTTP_CODE="):
            http_code = line.split("=", 1)[1].strip()
        elif line.startswith("FINAL_URL="):
            final_url = line.split("=", 1)[1].strip()
        elif line.startswith("REMOTE_IP="):
            remote_ip = line.split("=", 1)[1].strip()
        elif line.startswith("NUM_REDIRECTS="):
            num_redirects = line.split("=", 1)[1].strip()

    lines = [
        f"# Summary do run real mínimo",
        "",
        f"- collector_id: {collector_id}",
        f"- target: {target}",
        f"- resolved_ips: {', '.join(dns_ips) if dns_ips else 'nenhum'}",
        f"- hop_count: {len(hops)}",
        f"- final_url: {final_url}",
        f"- http_code: {http_code}",
        f"- remote_ip: {remote_ip}",
        f"- redirects: {num_redirects}",
        "",
        "## Leitura",
        "",
        "- A coleta produziu DNS, trace e evidência HTTP suficientes para ingestão mínima disciplinada.",
        "- O bundle foi emitido com `bundle_id` e `bundle_version` explícitos.",
        "- As relações observadas cobrem resolução de nome e precedência simples do caminho.",
    ]
    return "\n".join(lines) + "\n"


def build_run_manifest(
    *,
    run_id: str,
    collector_id: str,
    target_type: str,
    target_value: str,
    service_hint: str,
    scenario: str,
    started_at: datetime,
    finished_at: datetime,
    run_status: str,
    collection_health: str,
    tools_enabled: list[str],
    tools_succeeded: list[str],
    tools_failed: list[str],
    artifacts: list[dict[str, Any]],
    summary: str,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "collector_id": collector_id,
        "target_type": target_type,
        "target_value": target_value,
        "service_hint": service_hint,
        "scenario": scenario,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "run_status": run_status,
        "collection_health": collection_health,
        "summary": summary,
        "tools_enabled": tools_enabled,
        "tools_succeeded": tools_succeeded,
        "tools_failed": tools_failed,
        "artifacts": artifacts,
        "notes": [
            f"collector_id={collector_id}",
            f"bundle_id=pending",
            f"bundle_version={DEFAULT_BUNDLE_VERSION}",
            "first_real_layer0_collection",
        ],
        "tags": ["layer0", "real_collection", target_value, scenario],
        "scenario_version": "layer0-real-v1",
    }


def build_ingestion_bundle(
    *,
    run_id: str,
    bundle_id: str,
    bundle_version: str,
    collector_id: str,
    target_type: str,
    target_value: str,
    service_hint: str,
    scenario: str,
    started_at: datetime,
    finished_at: datetime,
    run_status: str,
    collection_health: str,
    observed_elements: list[dict[str, Any]],
    observed_relations: list[dict[str, Any]],
    artifacts_manifest: list[dict[str, Any]],
    notes: list[str],
    ingestion_level: str,
    rationale: str,
    blocking_issues: list[str],
) -> dict[str, Any]:
    return {
        "bundle_id": bundle_id,
        "bundle_version": bundle_version,
        "run_context": {
            "run_id": run_id,
            "collector_id": collector_id,
            "target_type": target_type,
            "target_value": target_value,
            "service_hint": service_hint,
            "scenario": scenario,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "run_status": run_status,
            "collection_health": collection_health,
        },
        "observed_elements": observed_elements,
        "observed_relations": observed_relations,
        "artifacts_manifest": artifacts_manifest,
        "ingestion_confidence": {
            "level": ingestion_level,
            "rationale": rationale,
            "blocking_issues": blocking_issues,
        },
        "notes": notes,
    }


def ingest_bundle(manifest_path: Path, bundle_path: Path, database_url: str) -> None:
    ingest_script = REPO_ROOT / "src" / "ingest_run_bundle.py"
    env = {**os.environ, "DATABASE_URL": database_url}
    if os.geteuid() == 0:
        cmd = [
            "runuser",
            "-u",
            "postgres",
            "--",
            "env",
            f"DATABASE_URL={database_url}",
            sys.executable,
            str(ingest_script),
            str(manifest_path),
            str(bundle_path),
        ]
    else:
        cmd = [
            sys.executable,
            str(ingest_script),
            str(manifest_path),
            str(bundle_path),
        ]
    subprocess.run(cmd, check=True, cwd=str(REPO_ROOT), env=env)


def main() -> int:
    parser = argparse.ArgumentParser(description="Coleta real mínima da Camada 0 do topomemory.")
    parser.add_argument("target", help="alvo da coleta, por exemplo example.com")
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--target-type", default=DEFAULT_TARGET_TYPE)
    parser.add_argument("--service-hint", default=DEFAULT_SERVICE_HINT)
    parser.add_argument("--collector-id", default=DEFAULT_COLLECTOR_ID)
    parser.add_argument("--bundle-version", default=DEFAULT_BUNDLE_VERSION)
    parser.add_argument("--bundle-id", default=None)
    parser.add_argument("--run-base-dir", default="runs")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    parser.add_argument("--skip-ingest", action="store_true")
    args = parser.parse_args()

    started_at = now_local()
    run_id = run_id_for(args.target, started_at)
    bundle_id = args.bundle_id or bundle_id_for(run_id)
    run_dir = REPO_ROOT / args.run_base_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    target_value = args.target.strip()
    target_url = target_value if re.match(r"^https?://", target_value) else f"https://{target_value}"

    tools_enabled = ["traceroute", "curl"]
    tools_succeeded: list[str] = []
    tools_failed: list[str] = []

    try:
        dns_result, dns_ips, dns_tool = resolve_dns(target_value, run_dir)
        if dns_tool not in tools_enabled:
            tools_enabled.append(dns_tool)
        if dns_result.returncode == 0 and dns_ips:
            tools_succeeded.append(dns_tool)
        else:
            tools_failed.append(dns_tool)

        trace_result, hops, trace_file_name = trace_route(target_value, run_dir)
        trace_tool = "traceroute" if trace_file_name == "traceroute.txt" else "mtr"
        if trace_tool not in tools_enabled:
            tools_enabled.append(trace_tool)
        if trace_result.returncode == 0 and hops:
            tools_succeeded.append(trace_tool)
        else:
            tools_failed.append(trace_tool)

        http_result = fetch_http(target_url, run_dir)
        if http_result.returncode == 0:
            tools_succeeded.append("curl")
        else:
            tools_failed.append("curl")

        if not dns_ips:
            raise CollectionError("DNS nao produziu enderecos utiliaveis")

        evidence_paths = {
            "dns": f"runs/{run_id}/dns.txt",
            "trace": f"runs/{run_id}/{trace_file_name}",
            "http": f"runs/{run_id}/http.txt",
        }

        observed_elements, observed_relations = build_observations(run_id, target_value, dns_ips, hops, evidence_paths)

        summary_md = build_summary(target_value, args.collector_id, dns_ips, hops, http_result)
        summary_path = run_dir / "summary.md"
        text_dump(summary_path, summary_md)

        artifact_specs = [
            (
                "manifest",
                run_dir / "run_manifest.json",
                "registro oficial do run",
                "application/json",
                None,
            ),
            (
                "ingestion_bundle",
                run_dir / "ingestion_bundle.json",
                "pacote oficial de entrada da Camada 1",
                "application/json",
                None,
            ),
            (
                "dns_capture",
                run_dir / "dns.txt",
                "resolucao DNS real do alvo",
                "text/plain",
                sha256_file(run_dir / "dns.txt"),
            ),
            (
                "traceroute_capture",
                run_dir / trace_file_name,
                "trace real minimo da rota",
                "text/plain",
                sha256_file(run_dir / trace_file_name),
            ),
            (
                "http_capture",
                run_dir / "http.txt",
                "evidencia HTTP/URL final",
                "text/plain",
                sha256_file(run_dir / "http.txt"),
            ),
            (
                "summary",
                summary_path,
                "resumo curto do run",
                "text/markdown",
                sha256_file(summary_path),
            ),
        ]

        finished_at = now_local()
        run_status = "success" if not tools_failed else "partial"
        collection_health = "healthy" if not tools_failed else "degraded"
        manifest_artifacts = [
            make_artifact(run_id, kind, path, purpose, finished_at, mime_type, sha256)
            for kind, path, purpose, mime_type, sha256 in artifact_specs
        ]

        manifest = build_run_manifest(
            run_id=run_id,
            collector_id=args.collector_id,
            target_type=args.target_type,
            target_value=target_value,
            service_hint=args.service_hint,
            scenario=args.scenario,
            started_at=started_at,
            finished_at=finished_at,
            run_status=run_status,
            collection_health=collection_health,
            tools_enabled=tools_enabled,
            tools_succeeded=tools_succeeded,
            tools_failed=tools_failed,
            artifacts=manifest_artifacts,
            summary=summary_md.strip(),
        )
        manifest["notes"] = [
            f"collector_id={args.collector_id}",
            f"target={target_value}",
            f"run_dir={run_dir.as_posix()}",
            f"bundle_id={bundle_id}",
            f"bundle_version={args.bundle_version}",
            "real_minimal_collection_from_layer0",
        ]

        bundle_artifacts_manifest = [
            {
                "artifact_id": item["artifact_id"],
                "kind": item["kind"],
                "path": item["path"],
                "purpose": item["purpose"],
                **({"sha256": item["sha256"]} if "sha256" in item else {}),
                **({"mime_type": item["mime_type"]} if "mime_type" in item else {}),
            }
            for item in manifest_artifacts
        ]

        bundle_level = "minimal"
        blocking_issues: list[str] = []
        if tools_failed:
            blocking_issues = [f"ferramenta sem saida util: {tool}" for tool in tools_failed]
        rationale = "coleta real minima com DNS, trace e HTTP para alvo publico simples"
        bundle = build_ingestion_bundle(
            run_id=run_id,
            bundle_id=bundle_id,
            bundle_version=args.bundle_version,
            collector_id=args.collector_id,
            target_type=args.target_type,
            target_value=target_value,
            service_hint=args.service_hint,
            scenario=args.scenario,
            started_at=started_at,
            finished_at=finished_at,
            run_status=run_status,
            collection_health=collection_health,
            observed_elements=observed_elements,
            observed_relations=observed_relations,
            artifacts_manifest=bundle_artifacts_manifest,
            notes=[
                f"bundle_id={bundle_id}",
                f"bundle_version={args.bundle_version}",
                f"collector_id={args.collector_id}",
                f"target={target_value}",
                "camada_1_fechada_nesta_rodada",
            ],
            ingestion_level=bundle_level,
            rationale=rationale,
            blocking_issues=blocking_issues,
        )

        manifest_path = run_dir / "run_manifest.json"
        bundle_path = run_dir / "ingestion_bundle.json"
        json_dump(manifest_path, manifest)
        json_dump(bundle_path, bundle)

        if not args.skip_ingest:
            ingest_bundle(manifest_path, bundle_path, args.database_url)

        print(json.dumps(
            {
                "run_id": run_id,
                "bundle_id": bundle_id,
                "run_dir": run_dir.as_posix(),
                "target": target_value,
                "collector_id": args.collector_id,
                "run_status": run_status,
                "collection_health": collection_health,
                "bundle_version": args.bundle_version,
                "artifacts": [item["path"] for item in manifest_artifacts],
                "ingested": not args.skip_ingest,
            },
            ensure_ascii=False,
            indent=2,
        ))
        return 0
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
