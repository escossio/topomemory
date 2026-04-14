# Comparação baseline vs provider real

## Baseline congelado

- provider: `hash`
- model: `topomemory-hash-embedding-v1`
- total_queries: `12`
- total_pass: `11`
- total_fail: `1`
- hit_rate: `0.9166666666666666`
- mean_first_hit_position: `1`
- falha útil: `q12_private_hop_google`

## Provider real tentado

- provider: `openai`
- credencial reutilizada de: `/etc/livecopilot-semantic.env` via `livecopilot-semantic-api.service`
- estado: ativo e executado com sucesso
- modelo: `text-embedding-3-small`
- elementos reindexados: `40`

## Resultado medido

- total_queries: `12`
- total_pass: `8`
- total_fail: `4`
- hit_rate: `0.6666666666666666`
- mean_first_hit_position: `1`
- q12_private_hop_google: `pass`

## Resultado

- reindexação: executada
- benchmark: reexecutado com provider real
- comparação de qualidade: disponível e pior que o baseline hash no agregado
