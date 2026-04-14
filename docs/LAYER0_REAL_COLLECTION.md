# Coleta real mínima da Camada 0

## Objetivo

Esta rodada prova a primeira coleta real mínima da Camada 0 usando a origem oficial `vm-10.45.0.4`, com um alvo público simples, artefatos reais e ingestão persistida no PostgreSQL.

## Alvo escolhido

- `example.com`
- cenário funcional: `home_page`
- tipo de alvo: `domain`
- pista de serviço: `public_home_page`

## Ferramenta mínima usada

- `dig`, `host` ou `getent` para resolução DNS real
- `traceroute` para trace mínimo real
- `curl` para evidência HTTP e URL final

## Script de coleta

- `src/collect_minimal_run.py`

O script:

- gera um `run_id` único
- usa `collector_id = vm-10.45.0.4`
- cria `runs/<run_id>/`
- salva `dns.txt`, `traceroute.txt` ou `mtr.txt`, `http.txt`, `summary.md`
- gera `run_manifest.json`
- gera `ingestion_bundle.json`
- emite `bundle_id` e `bundle_version` explicitamente
- faz fallback de DNS quando `dig` não existir no host
- repassa `DATABASE_URL` explicitamente para o CLI de ingestão mesmo fora de `root`
- chama `src/ingest_run_bundle.py` ao final, salvo `--skip-ingest`

## Como rodar

```bash
python3 src/collect_minimal_run.py example.com
```

Se precisar sobrescrever o banco:

```bash
python3 src/collect_minimal_run.py example.com \
  --database-url 'postgresql:///livecopilot?host=/var/run/postgresql'
```

## Prova literal na VM `10.45.0.4`

Fluxo mínimo validado:

- acesso canônico por `ssh -i /lab/projects/livecopilot/lab/vms/livecopilot-validation/admin_sshkey codex@10.45.0.4`
- pasta temporária limpa na VM: `/tmp/topomemory-runner`
- cópia mínima usada na VM:
  - `src/collect_minimal_run.py`
  - `src/ingest_run_bundle.py`
- alvo mantido em `example.com`
- cenário mantido em `home_page`

Se o PostgreSQL estiver escutando apenas em `127.0.0.1` no host de origem, use um túnel SSH reverso para expor a porta local na VM:

```bash
ssh -fNT -R 15432:127.0.0.1:5432 \
  -i /lab/projects/livecopilot/lab/vms/livecopilot-validation/admin_sshkey \
  codex@10.45.0.4
```

Depois rode a coleta literal na VM apontando para a porta tunelada:

```bash
python3 src/collect_minimal_run.py example.com \
  --database-url 'postgresql://<usuario>:<senha>@127.0.0.1:15432/livecopilot'
```

## Diretório de run

- `runs/<run_id>/`

Exemplo de conteúdo:

- `run_manifest.json`
- `ingestion_bundle.json`
- `dns.txt`
- `traceroute.txt`
- `http.txt`
- `summary.md`

## Como o bundle foi mapeado

- `run_manifest.artifacts` inventaria os artefatos gerados pelo run
- `ingestion_bundle.artifacts_manifest` referencia os mesmos artefatos, com os campos mínimos da fronteira da Camada 1
- `observed_elements` registra o alvo, os IPs resolvidos e os hops observados
- `observed_relations` registra a resolução DNS e a ordem simples do caminho

## Persistência

O script chama o CLI existente:

- `src/ingest_run_bundle.py`

O CLI persiste:

- `topomemory.run`
- `topomemory.run_artifact`
- `topomemory.ingestion_bundle`

## Validação no banco

Depois da ingestão, valide com consultas objetivas:

```sql
SELECT run_id, collector_id, target_value, run_status, collection_health
FROM topomemory.run
WHERE run_id = '<run_id>';

SELECT artifact_id, artifact_type, artifact_path, artifact_status
FROM topomemory.run_artifact
WHERE run_id = '<run_id>'
ORDER BY artifact_id;

SELECT bundle_id, bundle_version, ingestion_confidence
FROM topomemory.ingestion_bundle
WHERE run_id = '<run_id>';
```

## Limitações desta primeira prova

- O foco é a coleta mínima, não a normalização da Camada 1.
- O browser completo e DevTools continuam fora do escopo.
- O bundle continua sendo a única porta oficial de entrada da Camada 1.
- Se o trace real variar, o run ainda deve permanecer auditável pelos artefatos salvos.
- Se o role de aplicação ainda não tiver acesso ao schema `topomemory`, a ingestão falha até o `GRANT` mínimo ser aplicado.
