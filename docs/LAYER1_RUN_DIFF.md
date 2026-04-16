# Comparação entre runs da Camada 1

## Propósito

A comparação entre runs da Camada 1 existe para mostrar, de forma analítica, o que se repete, o que muda e como os caminhos observados se diferenciam entre duas coletas já consolidadas.

Ela não altera a identidade canônica. Ela só compara o resultado consolidado.

## O que a view mostra

A superfície SQL base `topomemory.v_layer1_run_elements` expõe, por linha:

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
- `comparison_basis`
- `comparison_key`
- `observational_signature`
- `resolved_ip_scope`
- `observed_at`
- `canonical_ip`
- `canonical_hostname`
- `canonical_asn`
- `canonical_org`
- `role_hint_current`
- `first_seen_at`
- `last_seen_at`

A regra de comparação é:

1. prioridade para `resolved_element_id` quando ele existir
2. fallback para `comparison_key` baseado em assinatura observacional quando não houver `resolved_element_id`
3. `skipped_*` entram como divergência observacional, não como erro

A view agregada `topomemory.v_layer1_run_diff_summary` resume cada run com contagens e sequências.

## O que o CLI mostra

O script `src/report_layer1_run_diff.py` compara dois `run_id` e imprime:

- total de `observed_elements` em cada run
- total de `network_elements` resolvidos em cada run
- quantos elementos são comuns
- quantos são exclusivos do run A
- quantos são exclusivos do run B
- distribuição `public/private` por run
- prefixo comum da sequência de hops, quando existir
- leitura curta de estabilidade, diversidade e diferença principal

Com `--show-common`, `--show-unique` e `--show-path`, ele também lista as linhas e as sequências comparadas.

## Como executar

Exemplo:

```bash
DATABASE_URL='postgresql:///topomemory?host=/var/run/postgresql' \
  python3 src/report_layer1_run_diff.py \
  --run-a 'run-20260414T165621+0000-example-com-03efa5c6' \
  --run-b 'run-20260414T170024+0000-google-com-d99305f2' \
  --show-path
```

## Papel antes da camada semântica

Esta superfície de diff fica antes de embeddings, `pgvector` e grafo operacional.

Ela ajuda a comparar caminhos reais já consolidados sem mudar o baseline.

## Limitações atuais

- não cria nem altera `observed_element`
- não cria nem altera `identity_decision`
- não cria nem altera `network_element`
- não introduz scoring pesado de recorrência
- não altera as regras de identidade mínimas
- não substitui a auditoria por run/bundle

## Relação com o baseline e com a auditoria

O baseline continua em [LAYER1_BASELINE.md](/docs/LAYER1_BASELINE.md).
A auditoria operacional continua em [LAYER1_AUDIT.md](/docs/LAYER1_AUDIT.md).

A comparação entre runs lê os resultados já consolidados e os coloca lado a lado para análise.

## Relação com a Camada 2

A mesma leitura por `run_id` usada aqui alimenta a Camada 2 mínima:

- o caminho observado vira `path_signature`
- a identidade resolvida vira `resolved_path_signature`
- a comparação entre runs equivalentes alimenta a avaliação de saúde da rota
