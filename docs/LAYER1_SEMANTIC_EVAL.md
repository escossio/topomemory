# Avaliação da busca semântica da Camada 1

## Objetivo

Medir, com critérios reproduzíveis, a utilidade inicial da busca semântica auxiliar sobre `network_element`.

Esta avaliação não altera a identidade canônica da Camada 1. Ela serve apenas para medir o baseline atual antes de trocar o motor de embedding.

## Por que esta avaliação vem antes de trocar o motor

- o motor atual é determinístico e auditável
- a camada semântica ainda está em fase inicial
- antes de migrar para um motor mais forte, é preciso medir o comportamento atual
- um baseline explícito evita comparação subjetiva depois

## Tipos de query cobertos

- hostname/destino público
- elemento privado / hop
- atributos estruturais e organizacionais
- casos combinados com mistura de público e privado

## Regras de expectativa

Cada query usa uma expectativa mínima auditável.

Modos suportados:

- `top1_expected`
- `topk_contains`
- `category_contains`

O dataset também registra:

- `expected_element_ids`
- `expected_label_contains`
- `expected_categories`
- `notes`

## Como rodar o benchmark

```bash
set -euo pipefail
PW=$(cat "$HOME/topomemory_app.password")
export DATABASE_URL="postgresql://topomemory_app:${PW}@10.45.0.3:5432/topomemory"
export TOPOMEMORY_EMBEDDING_PROVIDER=hash
python3 src/evaluate_semantic_search.py \
  --queries-file schemas/semantic_eval_queries.json \
  --limit 5 \
  --json-out artifacts/semantic-eval/latest_results.json \
  --markdown-out artifacts/semantic-eval/latest_report.md
```

## Como interpretar o relatório

- `hit_rate`: fração das queries que satisfizeram a expectativa
- `first_hit_position`: posição da primeira correspondência útil na lista retornada
- `top1`: primeiro resultado devolvido pelo motor
- `topk`: lista de retornos usados na avaliação

## Limitações do baseline atual

- o embedding atual é lexical-hash determinístico
- o provider ativo padrão é hash e permanece local
- um provider real `openai` pode ser ativado via `TOPOMEMORY_EMBEDDING_PROVIDER=openai` quando `OPENAI_API_KEY` estiver configurada
- a qualidade semântica ainda depende fortemente de termos literais presentes no perfil
- a avaliação não mede recall geral do banco
- a avaliação não muda a identidade determinística
- a avaliação não usa LLM externo

## Leitura esperada

Este benchmark deve ser usado como referência comparativa para futuros motores mais fortes, mantendo o mesmo dataset e a mesma metodologia sempre que possível.
