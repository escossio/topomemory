# Conceito de banco

## Base escolhida

O banco principal do projeto é `PostgreSQL + pgvector`.

## Princípio de separação

O modelo separa observação bruta de entidade canônica. A mesma coisa observada várias vezes pode gerar múltiplas observações, mas converge para uma identidade canônica quando o sistema decide isso com base em evidências.

## Blocos principais do modelo

- `collector`
- `run`
- `network_element`
- `network_observation`
- `observation_relation`
- `element_relation`
- `identity_decision`
- `element_role_history`
- `service_identity`
- `service_delivery_observation`
- `route_observation`
- `route_membership`

## Observação

Este documento descreve apenas o modelo conceitual inicial. Não é o schema SQL definitivo e não substitui decisões de implementação futura.

