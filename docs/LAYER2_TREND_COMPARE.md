# Comparação mínima entre janelas da Camada 2

## Objetivo

A comparação mínima entre janelas da Camada 2 responde se o comportamento recente de uma rota está melhorando, piorando ou permanecendo equivalente entre duas janelas sucessivas.

Ela continua fora de Prometheus, fora de UI e fora da camada de incidente.

## Contrato da comparação

A frente grava `route_health_trend_compare` com:

- `current_trend_id`
- `previous_trend_id`
- `public_trend_delta`
- `private_trend_delta`
- `destination_trend_delta`
- `overall_trend_delta`
- `confidence`
- `reasoning_summary`
- `evidence_json`

## Janela usada

Esta primeira versão compara a janela atual contra a janela anterior imediatamente disponível para o mesmo `target_value` e `scenario`.

Quando a história é curta, a comparação usa janelas unitárias para manter a leitura sucessiva honesta com a base disponível.

## Regras mínimas

- `public_trend_delta = improved` quando o trecho público melhora em relação à janela anterior
- `public_trend_delta = worsened` quando o trecho público piora
- `private_trend_delta = improved` quando a oscilação privada diminui
- `private_trend_delta = worsened` quando a oscilação privada aumenta
- `destination_trend_delta = changed` quando o destino muda
- `overall_trend_delta = improving` quando a leitura geral melhora sem regressão forte
- `overall_trend_delta = worsening` quando há piora relevante em saúde, público ou destino
- `overall_trend_delta = unchanged` quando a janela nova permanece equivalente
- `overall_trend_delta = insufficient_context` quando não há base suficiente

## O que esta frente não faz

- não cria série temporal completa
- não usa Prometheus
- não abre incidente final
- não altera a Camada 1

## Exemplo esperado

Para `google.com / home_page`, a comparação pode mostrar:

- destino estável
- delta público estável
- delta privado equivalente
- delta geral equivalente

Se não houver janela anterior suficiente, a leitura deve cair para `insufficient_context`.
