# Camada 2 mínima de saúde operacional da rota

## Objetivo

A Camada 2 mínima transforma runs já consolidados nas Camadas 0 e 1 em uma leitura operacional simples, persistente e auditável da saúde da rota.

Ela não abre incidentes, não aciona ação automática e não depende de Prometheus nesta rodada.

## O que é `route_snapshot`

`route_snapshot` é o resumo persistido de um run visto como rota.

Ele registra:

- o run e o bundle de origem
- target e scenario
- contagens mínimas de observação, resolução e decisão
- assinatura textual da rota observada
- assinatura textual da rota resolvida
- melhor candidato atual a destino final
- notas curtas sobre o contexto do snapshot

## O que é `route_health_assessment`

`route_health_assessment` é a leitura operacional mínima derivada do snapshot.

Ela registra:

- `health_status`
- `structural_status`
- `route_change_status`
- nível de confiança
- resumo de reasoning
- evidência em JSON
- comparação opcional com outro run

## Regras mínimas de classificação

Nesta primeira versão:

- `healthy` é usado quando o run foi bem coletado, a rota ficou suficientemente resolvida e o destino ficou claro
- `degraded` é usado quando há sinal útil, mas a resolução ficou parcial ou o destino ficou fraco
- `blocked` é usado quando o run foi interrompido, falhou ou ficou operacionalmente bloqueado
- `unknown` é usado quando a leitura seria especulativa demais

## Regras mínimas de comparação

Comparação só faz sentido entre runs equivalentes, isto é:

- mesmo `target_value`
- mesmo `scenario`

Os estados mínimos são:

- `first_observation` quando não há equivalente anterior útil
- `unchanged` quando a assinatura resolvida é igual
- `changed` quando a assinatura resolvida muda com material suficiente
- `not_comparable` quando o contexto não permite afirmar

## O que esta rodada não faz

- não abre Prometheus
- não cria incidente
- não aciona ação automática
- não cria grafo operacional
- não altera identidade determinística
- não mexe na Camada 0
- não altera a semântica auxiliar

## Relação com a Camada 3

A Camada 3 futura deve trazer temporalidade mais rica e séries observáveis.

Esta camada mínima prepara o terreno ao guardar:

- snapshots por run
- avaliações derivadas
- comparação entre runs equivalentes

## Exemplos de leitura

Um run de `google.com / home_page` pode resultar em snapshot com destino explícito e avaliação `healthy`.

Um run equivalente anterior com a mesma assinatura resolvida pode resultar em `unchanged`.

Um run de `example.com / home_page` pode servir como primeira observação equivalente ou como caso sem comparação útil, dependendo do histórico disponível.
