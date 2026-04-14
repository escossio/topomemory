# Ingestão mínima da Camada 0

## Propósito

Esta rotina prova o caminho mínimo de persistência da Camada 0:

- lê um `run_manifest`
- lê um `ingestion_bundle`
- valida consistência básica
- persiste `run`, `run_artifact` e `ingestion_bundle`

O script não implementa a coleta real. Ele só fecha a prova de contrato entre os JSONs de referência e as tabelas da Camada 0.

## Entradas esperadas

- `run_manifest` em JSON
- `ingestion_bundle` em JSON

Os exemplos de referência do repositório são:

- [schemas/run_manifest.example.json](/schemas/run_manifest.example.json)
- [schemas/ingestion_bundle.example.json](/schemas/ingestion_bundle.example.json)

## Variável de ambiente

- `DATABASE_URL`: string de conexão do PostgreSQL já existente

## Comando de execução

```bash
DATABASE_URL='postgresql:///NOME_DO_BANCO?host=/var/run/postgresql' \
  python3 src/ingest_run_bundle.py \
  schemas/run_manifest.example.json \
  schemas/ingestion_bundle.example.json
```

## O que o script valida

- JSON válido nos dois arquivos
- presença dos campos mínimos do run
- coerência entre `run_id` do manifest e `run_context.run_id` do bundle
- coerência entre `collector_id` do manifest e `run_context.collector_id` do bundle
- existência prévia do `collector_id` na tabela `topomemory.collector`
- `ingestion_confidence.level` compatível com a camada atual
- timestamp mínimo e ordem temporal do run

## O que ele persiste

- `topomemory.run`
- `topomemory.run_artifact`
- `topomemory.ingestion_bundle`

### Regra de persistência

- `run` é feito por `run_id` com upsert
- `run_artifact` é reconstruído a partir de `run_manifest.artifacts`
- `ingestion_bundle` é feito por `run_id` com upsert
- `bundle_id` é derivado de `run_id` quando o JSON não traz um valor explícito
- `bundle_version` usa `layer0-v1` quando o JSON não traz um valor explícito

## Limitações desta primeira versão

- Não há coletor real.
- Não há browser, tcpdump ou MTR.
- `observed_elements` e `observed_relations` continuam serializados em JSONB.
- O script não cria tabelas nem roda migrations.
- O script assume que a migration baseline e a seed do collector já foram aplicadas.

## Como verificar no banco

Depois da execução, valide com consultas como:

```sql
SELECT * FROM topomemory.run WHERE run_id = 'run-2026-04-14-001';
SELECT * FROM topomemory.run_artifact WHERE run_id = 'run-2026-04-14-001';
SELECT * FROM topomemory.ingestion_bundle WHERE run_id = 'run-2026-04-14-001';
SELECT * FROM topomemory.collector WHERE collector_id = 'vm-10.45.0.4';
```

## Observação

Se o `collector_id` não existir, o script falha antes de inserir qualquer dado.
Se `run_id` do manifest e do bundle não baterem, a transação é abortada.
