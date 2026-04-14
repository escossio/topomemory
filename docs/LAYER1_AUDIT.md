# Auditoria operacional da Camada 1

## Propósito

A auditoria operacional da Camada 1 existe para inspecionar, com leitura direta e rastreável, como cada `observed_element` foi tratado pelo baseline mínimo de identidade.

Ela não muda as regras de consolidação. Ela só torna visível o resultado delas por `run_id` e `bundle_id`.

## O que a view mostra

A visão SQL `topomemory.v_layer1_identity_audit` expõe, por linha:

- `run_id`
- `bundle_id`
- `observed_element_id`
- `element_index`
- `observed_ip`
- `observed_hostname`
- `observed_ptr`
- `observed_ip_scope`
- `hop_index`
- `service_context`
- `decision_type`
- `confidence`
- `reasoning_summary`
- `matched_element_id`
- `new_element_id`
- `resolved_element_id`
- `ip_scope`
- `observed_at`
- `canonical_ip`
- `canonical_hostname`
- `canonical_asn`
- `canonical_org`
- `role_hint_current`
- `first_seen_at`
- `last_seen_at`

O campo `resolved_element_id` aponta para o `network_element` final quando houver `matched_element_id` ou `new_element_id`. Quando a decisão for `skipped_*`, o mapeamento final fica nulo.

## O que o CLI mostra

O script `src/report_layer1_audit.py` lê a view e imprime:

- total de `observed_elements`
- quantos `matched_existing_entity`
- quantos `new_entity_created`
- quantos `skipped_*`
- quantos resolvidos como `public`
- quantos resolvidos como `private`
- lista detalhada por linha, quando `--summary-only` não for usado

## Como executar

Exemplos:

```bash
DATABASE_URL='postgresql:///topomemory?host=/var/run/postgresql' \
  python3 src/report_layer1_audit.py --run-id 'run-20260414T165621+0000-example-com-03efa5c6'
```

```bash
DATABASE_URL='postgresql:///topomemory?host=/var/run/postgresql' \
  python3 src/report_layer1_audit.py --bundle-id 'bundle-run-20260414T170024+0000-google-com-d99305f2' --summary-only
```

## Papel antes da camada semântica

Esta superfície de auditoria é a etapa seguinte à Camada 1 baseline: ela dá visibilidade operacional para os casos reais antes de abrir embeddings, `pgvector` ou qualquer merge semântico.

## Limitações atuais

- não cria nem altera `observed_element`
- não cria nem altera `identity_decision`
- não cria nem altera `network_element`
- não substitui a validação da Camada 0
- não adiciona heurística nova de identidade
- não cobre runs sem decisão consolidada, além de mostrar o vazio como ausência de linhas

## Relação com o baseline

O baseline mínimo continua em [LAYER1_BASELINE.md](/docs/LAYER1_BASELINE.md).

A auditoria só lê o resultado desse baseline e organiza a leitura por run, bundle e observação.
