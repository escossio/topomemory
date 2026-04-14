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
- estado: bloqueado por credencial ausente
- erro observado: `OPENAI_API_KEY` ausente

## Resultado

- reindexação: não executada
- benchmark: não reexecutado com provider real
- comparação de qualidade: indisponível até a configuração da credencial

