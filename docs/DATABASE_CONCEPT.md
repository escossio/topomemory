# Conceito de banco

## Base escolhida

O banco principal do projeto é `PostgreSQL + pgvector`.

## Princípio de separação

O modelo separa observação bruta de entidade canônica. A mesma coisa observada várias vezes pode gerar múltiplas observações, mas converge para uma identidade canônica quando o sistema decide isso com base em evidências.

## Camada 0: schema conceitual próprio

A Camada 0 já possui um schema conceitual persistível separado, documentado em [COLLECTION_SCHEMA_CONCEPT.md](/docs/COLLECTION_SCHEMA_CONCEPT.md).

## Blocos principais da Camada 0

- `collector`
- `run`
- `run_artifact`
- `ingestion_bundle`
- `observed_element_stub` (futuro, se necessário)
- `observed_relation_stub` (futuro, se necessário)

## Observação

Este documento descreve apenas o modelo conceitual inicial. Não é o schema SQL definitivo e não substitui decisões de implementação futura.
