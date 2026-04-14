# Notas do SQL inicial da Camada 0

## Escopo

Este documento registra as escolhas do primeiro SQL inicial da Camada 0, definido em [sql/001_layer0_initial.sql](/sql/001_layer0_initial.sql).
A forma versionada oficial da baseline agora está em [sql/migrations/001_layer0_initial.up.sql](/sql/migrations/001_layer0_initial.up.sql).
Ele cobre apenas as entidades mínimas necessárias para a persistência inicial:

- `collector`
- `run`
- `run_artifact`
- `ingestion_bundle`

## Tabelas criadas

- `collector`: origem controlada da coleta.
- `run`: execução delimitada e auditável da observação.
- `run_artifact`: inventário dos artefatos produzidos por um run.
- `ingestion_bundle`: pacote oficial de entrada da Camada 1.

## JSONB nesta fase

Os seguintes campos ficaram em `JSONB` para preservar a fronteira entre persistência relacional mínima e blocos ainda não normalizados:

- `collector.network_context`
- `run.tags_json`
- `ingestion_bundle.run_context_json`
- `ingestion_bundle.observed_elements_json`
- `ingestion_bundle.observed_relations_json`
- `ingestion_bundle.artifacts_manifest_json`

Motivos:

- `network_context` pode variar por ambiente e topologia.
- `tags_json` é um conjunto livre de marcadores, não uma entidade canônica.
- `run_context_json` replica o contexto serializável do bundle sem forçar duplicação relacional.
- `observed_elements_json` e `observed_relations_json` continuam como fronteira entre observação e canonização.
- `artifacts_manifest_json` mantém o pacote de entrada da Camada 1 coerente com os contratos já publicados.

## Normalização futura

Ficam para uma fase posterior:

- normalização de `observed_elements_json`
- normalização de `observed_relations_json`
- eventual extração de artefatos mais ricos a partir do manifesto
- revisão de campos opcionais quando a Camada 1 exigir identidade canônica mais estável

## Relação com os contratos documentados

O SQL inicial foi escrito para bater com:

- [docs/RUN_CONTRACT.md](/docs/RUN_CONTRACT.md)
- [docs/INGESTION_BUNDLE.md](/docs/INGESTION_BUNDLE.md)
- [docs/RUN_MANIFEST_FORMAT.md](/docs/RUN_MANIFEST_FORMAT.md)
- [docs/INGESTION_BUNDLE_FORMAT.md](/docs/INGESTION_BUNDLE_FORMAT.md)
- [docs/COLLECTION_SCHEMA_CONCEPT.md](/docs/COLLECTION_SCHEMA_CONCEPT.md)

## Limitações conhecidas

- Não há migrations adicionais além da baseline versionada.
- A baseline oficial versionada é a migration `001_layer0_initial.up.sql`.
- Não há seed de dados.
- Não há lógica de aplicação para manter `updated_at`; o SQL inicial usa trigger.
- Não há normalização da Camada 1.
- O SQL inicial é deliberadamente simples e evolutivo, não definitivo.
