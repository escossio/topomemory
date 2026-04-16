# Tendência temporal mínima da Camada 2

## Objetivo

A tendência temporal mínima da Camada 2 resume o comportamento recente de uma rota ao longo de vários runs equivalentes.

Ela não substitui Prometheus, não cria score pesado e não abre incidente final.

## Janela usada

Esta primeira versão usa uma janela curta e explícita:

- os últimos `3` runs equivalentes por `target_value` e `scenario`
- quando houver menos de `2` runs, a leitura cai para contexto insuficiente

## O que é `route_health_trend`

`route_health_trend` é o resumo persistido do comportamento recente de um grupo equivalente.

Ele guarda:

- `public_stability_status`
- `private_variation_status`
- `destination_stability_status`
- `overall_trend_status`
- `confidence`
- `reasoning_summary`
- evidência agregada em JSON

## Regras mínimas de leitura

- `public_stability_status = stable` quando o trecho público resolvido permanece igual na janela
- `private_variation_status = oscillating` quando o trecho público está estável e o trecho privado varia de forma recorrente
- `destination_stability_status = stable` quando o destino final permanece igual
- `overall_trend_status = stable` quando destino e trecho público ficam estáveis e a variação privada é baixa
- `overall_trend_status = oscillating` quando destino e trecho público ficam estáveis e a variação privada se repete
- `overall_trend_status = degrading` quando há sinal real de piora em saúde, destino ou trecho público
- `overall_trend_status = insufficient_context` quando a janela não permite uma leitura honesta

## O que esta frente não faz

- não modela série temporal completa
- não usa Prometheus
- não aciona incidente
- não altera a Camada 1
- não reabre a frente semântica

## Exemplo esperado

Para o grupo `google.com / home_page`, a leitura esperada é:

- destino estável
- trecho público estável
- trecho privado oscilando
- tendência geral `oscillating` ou `stable`, conforme a janela e a regra aplicada
