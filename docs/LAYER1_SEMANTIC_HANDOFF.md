# Handoff final da camada semântica da Camada 1

## Estado final da frente

Esta frente foi encerrada neste ciclo com a variante `hybrid_private_page8_focus` congelada como baseline ativo da camada semântica auxiliar.

O resultado final documentado é `12/12`, com `hit_rate = 1.0`, sem qualquer alteração na identidade determinística da Camada 1.

## Configuração ativa

- provider ativo: `openai`
- modelo ativo: `text-embedding-3-small`
- variante ativa: `hybrid_private_page8_focus`
- baseline ativo: `hybrid_private_page8_focus`
- benchmark fixo oficial: `12/12`

## Linha de decisão desta consolidação

- baseline anterior hash: `11/12`, `hit_rate = 0.9166666666666666`
- baseline openai inicial: `hybrid`, com `11/12`
- tuning vencedor: `hybrid_private_page8_focus`
- ajuste efetivo: reindexação localizada de apenas `1` elemento privado

## O que permaneceu intacto

- identidade determinística
- `semantic_profile_text`
- dataset de benchmark
- Camada 0
- grafo público
- BGP público

## Limitações restantes

- existe ruído residual de ranking em alguns casos
- a busca semântica ainda é auxiliar e não substitui a verdade canônica
- o benchmark fixo cobre 12 queries e não mede recall total do banco

## Próximo passo sugerido

Reabrir ranking só se houver novo escopo explícito para mexer na camada semântica ou trocar o motor; fora isso, manter este estado como baseline estável.
