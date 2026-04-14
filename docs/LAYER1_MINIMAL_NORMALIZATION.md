# Normalização mínima da Camada 1

## Objetivo

Transformar os blocos serializados `observed_elements` e `observed_relations` do `ingestion_bundle` em persistência relacional mínima própria, sem iniciar ainda correlação canônica avançada.

## Fronteira

Nesta etapa:

- `observed_element` e `observed_relation` pertencem ao `bundle` e ao `run`
- `element_index` e `relation_index` preservam a identidade local dentro do bundle
- `raw_json` é preservado para auditoria
- a Camada 1 ainda é apenas `observação normalizada`
- a entidade canônica consolidada continua para uma etapa posterior

## Tabelas

### `topomemory.observed_element`

Campos principais:

- `observed_element_id`
- `bundle_id`
- `run_id`
- `element_index`
- `observed_ip`
- `observed_hostname`
- `observed_ptr`
- `observed_asn`
- `observed_org`
- `ip_scope`
- `hop_index`
- `service_context`
- `source_type`
- `observed_at`
- `raw_json`

### `topomemory.observed_relation`

Campos principais:

- `observed_relation_id`
- `bundle_id`
- `run_id`
- `relation_index`
- `from_element_index`
- `to_element_index`
- `relation_type`
- `relation_order`
- `confidence_hint`
- `raw_json`

## Script de expansão

- [src/expand_bundle_to_observations.py](/src/expand_bundle_to_observations.py)

Entrada:

- `--run-id` ou `--bundle-id`
- `DATABASE_URL`

Saída:

- uma expansão idempotente por bundle
- observações normalizadas vinculadas ao bundle e ao run

## Validação

Depois da expansão, a leitura mínima esperada é:

- contagem de linhas por `run_id`
- vínculo de cada linha com `bundle_id`
- acesso ao `raw_json` para auditoria

## Limite intencional

Não há ainda:

- correlação canônica de entidades
- unificação de elementos repetidos entre runs
- embedding
- grafo operacional
