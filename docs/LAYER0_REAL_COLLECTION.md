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
- `scripts/run_layer0_remote.sh`

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
- pode ser executado por `scripts/run_layer0_remote.sh` para envio controlado ao host oficial

## Como rodar

```bash
python3 src/collect_minimal_run.py example.com
```

Se precisar sobrescrever o banco:

```bash
python3 src/collect_minimal_run.py example.com \
  --database-url 'postgresql://topomemory_app:<senha>@10.45.0.3:5432/topomemory'
```

## Prova literal na VM `10.45.0.4`

Fluxo mínimo validado:

- execução canônica na VM `10.45.0.4` via `scripts/run_layer0_remote.sh`
- SSH usado só para executar comandos e transferir os arquivos mínimos
- sem túnel SSH em qualquer ponto do fluxo
- pasta temporária limpa na VM: `/tmp/topomemory-runner`
- envio mínimo usado na VM:
  - `src/collect_minimal_run.py`
  - `src/ingest_run_bundle.py`
  - via `tar` controlado por `scripts/run_layer0_remote.sh`
- alvo mantido em `example.com`
- cenário mantido em `home_page`

Agora a coleta literal na VM aponta direto para o host PostgreSQL na rede interna:

```bash
python3 src/collect_minimal_run.py example.com \
  --database-url 'postgresql://topomemory_app:<senha>@10.45.0.3:5432/topomemory'
```

O caminho oficial não depende de `ssh -L`, `ssh -R` nem de qualquer túnel para o banco.

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

## Bootstrap operacional

O procedimento formal do fluxo endurecido está em:

- [docs/LAYER0_OPERATIONAL_BOOTSTRAP.md](/docs/LAYER0_OPERATIONAL_BOOTSTRAP.md)

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
- Se o role `topomemory_app` ainda não tiver acesso ao schema `topomemory`, a ingestão falha até o bootstrap oficial ser aplicado.
