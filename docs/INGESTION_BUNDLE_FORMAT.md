# Formato de referência do ingestion_bundle

## Propósito

`ingestion_bundle` é o pacote serializável de referência entregue pela Camada 0 para consumo exclusivo da Camada 1. Ele é a fronteira formal entre observação controlada e memória canônica.

## Blocos obrigatórios

- `run_context`
- `observed_elements`
- `observed_relations`
- `artifacts_manifest`
- `ingestion_confidence`

## Estrutura mínima dos blocos

### `run_context`

Contexto oficial do run.

Campos mínimos:

- `run_id` (`string`)
- `collector_id` (`string`)
- `target_type` (`string`)
- `target_value` (`string`)
- `service_hint` (`string`)
- `scenario` (`string`)
- `started_at` (`string`, RFC 3339)
- `finished_at` (`string`, RFC 3339)
- `run_status` (`string`)
- `collection_health` (`string`)

### `observed_elements`

Lista de elementos observados, ainda não canonizados.

Cada item deve conter, no mínimo:

- `observation_id` (`string`)
- `element_id` (`string`)
- `element_type` (`string`)
- `label` (`string`)
- `evidence_ref` (`string`)
- `confidence` (`number`, 0 a 1)

### `observed_relations`

Lista de relações observadas.

Cada item deve conter, no mínimo:

- `relation_id` (`string`)
- `from_element_id` (`string`)
- `to_element_id` (`string`)
- `relation_type` (`string`)
- `evidence_ref` (`string`)
- `confidence` (`number`, 0 a 1)

### `artifacts_manifest`

Inventário dos artefatos associados ao run.

Cada item deve conter, no mínimo:

- `artifact_id` (`string`)
- `kind` (`string`)
- `path` (`string`)
- `purpose` (`string`)

Campos opcionais:

- `sha256` (`string`)
- `mime_type` (`string`)

### `ingestion_confidence`

Leitura da confiança de ingestão.

Campos mínimos:

- `level` (`string`): `minimal`, `complete` ou `rejected`
- `rationale` (`string`): justificativa curta
- `blocking_issues` (`array<string>`): impedimentos relevantes, quando existirem

## Campos obrigatórios e opcionais

- `run_context`, `observed_elements`, `observed_relations`, `artifacts_manifest` e `ingestion_confidence` são obrigatórios.
- Dentro de cada bloco, os campos listados como mínimos são obrigatórios.
- Campos opcionais podem existir, mas não devem mudar o significado central do contrato.

## Regras de consistência

- `run_context.run_id` deve bater com o manifesto do run.
- `collector_id` deve identificar o mesmo coletor do manifesto.
- `observed_elements` e `observed_relations` devem ser internamente coerentes.
- `artifacts_manifest` deve referenciar artefatos ligados ao run.
- `ingestion_confidence.level` deve refletir a qualidade real do pacote.

## Quando o bundle é mínimo, completo ou rejeitado

- `minimal`: há contexto suficiente para ingestão parcial disciplinada.
- `complete`: há contexto, elementos, relações e artefatos suficientes para consumo confiável.
- `rejected`: falta coerência ou contexto básico para entrada na Camada 1.

## O que a Camada 1 pode assumir

Ao receber um `ingestion_bundle`, a Camada 1 pode assumir que:

- o contexto do run já está delimitado;
- os elementos observados já estão estruturados;
- as relações observadas já estão explicitadas;
- os artefatos relevantes já estão inventariados;
- a confiança de ingestão já foi classificada;
- não é necessário reconstruir o run a partir de arquivos dispersos.

## Exemplo de valores

- `run_context.collector_id`: `vm-10.45.0.4`
- `run_context.target_value`: `facebook.com`
- `run_context.scenario`: `home_page`
- `ingestion_confidence.level`: `minimal`

## Regra oficial

`ingestion_bundle` é a única interface oficial de entrada da Camada 1. A Camada 1 não deve consumir artefatos brutos como contrato primário.

