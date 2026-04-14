# Conceito de banco

## Base escolhida

O banco principal do projeto é `PostgreSQL + pgvector`.

## Decisão de infraestrutura

- O Topomemory reutiliza a instância PostgreSQL já existente no ambiente.
- Não haverá nova instância, serviço ou engine de banco nesta fase.
- A discussão atual é sobre escopo lógico dentro dessa mesma instância.

## Princípio de separação

O modelo separa observação bruta de entidade canônica. A mesma coisa observada várias vezes pode gerar múltiplas observações, mas converge para uma identidade canônica quando o sistema decide isso com base em evidências.

## Escopo lógico recomendado

### Recomendação padrão

- usar um database dedicado chamado `topomemory` dentro da instância PostgreSQL existente

### Alternativa aceita

- usar um schema dedicado `topomemory` em um database compartilhado, se houver restrição operacional para criar database dedicado

### Diferença prática

- `database dedicado`: separa catálogo, permissões, ownership e manutenção de forma mais clara
- `schema dedicado`: mantém o isolamento lógico dentro de um database já compartilhado, sem mudar a engine

### Critério de preferência

- a preferência é pelo database dedicado porque simplifica operação e reduz ambiguidade de ownership
- o schema dedicado não é erro; ele é fallback aceitável quando a infraestrutura exigir essa forma

## Camada 0: schema conceitual próprio

A Camada 0 já possui um schema conceitual persistível separado, documentado em [COLLECTION_SCHEMA_CONCEPT.md](/docs/COLLECTION_SCHEMA_CONCEPT.md).
Esse schema conceitual será persistido sobre a instância PostgreSQL já existente, mantendo isolamento lógico conforme a opção de escopo escolhida.

## Blocos principais da Camada 0

- `collector`
- `run`
- `run_artifact`
- `ingestion_bundle`
- `observed_element_stub` (futuro, se necessário)
- `observed_relation_stub` (futuro, se necessário)

## Observação

Este documento descreve apenas o modelo conceitual inicial. Não é o schema SQL definitivo e não substitui decisões de implementação futura.
