# Conceito de banco

## Base escolhida

O banco principal do projeto é `PostgreSQL + pgvector`, com database dedicado oficial `topomemory`.

## Decisão de infraestrutura

- O Topomemory reutiliza a instância PostgreSQL já existente no ambiente.
- Não haverá nova instância, serviço ou engine de banco nesta fase.
- A discussão atual é sobre escopo lógico dentro dessa mesma instância.
- O role oficial do projeto é `topomemory_app`.
- O schema oficial do projeto é `topomemory`.
- O acesso oficial usa a rede interna `10.45.0.0/16`.

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
O primeiro SQL inicial dessa camada está em [sql/001_layer0_initial.sql](/sql/001_layer0_initial.sql).
O estado operacional atual do projeto usa o database dedicado `topomemory` com owner `topomemory_app`.

## Blocos principais da Camada 0

- `collector`
- `run`
- `run_artifact`
- `ingestion_bundle`

## Camada 1 mínima: observações normalizadas

A primeira etapa relacional da Camada 1 normaliza as observações já persistidas no `ingestion_bundle` em tabelas próprias, preservando o vínculo com `bundle_id` e `run_id` e mantendo o `raw_json` para auditoria.

- `observed_element`
- `observed_relation`

Nesta etapa ainda não há entidade canônica consolidada, correlação semântica ou grafo operacional.

## Camada 1 identidade mínima

A etapa seguinte adiciona as primeiras entidades canônicas mínimas e o registro auditável das decisões de identidade.

- `network_element`
- `identity_decision`

Nesta rodada:

- a consolidação automática entra apenas para observações públicas
- IP privado ou reservado fica fora da consolidação automática
- a correspondência determinística inicial usa `canonical_ip`
- hostname/PTR pode formar uma identidade canônica complementar quando não houver IP canônico e o nome passar pela normalização conservadora
- hostname/PTR não substitui a identidade por IP público quando o IP existir
- IP privado pode formar identidade canônica apenas por vizinhança e posição local no bundle/run
- a decisão fica registrada com evidência e motivo textual

## Observação

Este documento descreve apenas o modelo conceitual inicial. Não é o schema SQL definitivo e não substitui decisões de implementação futura.
