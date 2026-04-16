# Conceito de banco

## Base escolhida

O banco principal do projeto é `PostgreSQL`.
A frente semântica auxiliar já usa `pgvector` de forma isolada, mas sem interferir na verdade canônica da Camada 1.

## Decisão de infraestrutura

- O Topomemory reutiliza a instância PostgreSQL já existente no ambiente.
- Não haverá nova instância, serviço ou engine de banco nesta fase.
- A discussão atual é sobre escopo lógico dentro dessa mesma instância.
- O role oficial do projeto é `topomemory_app`.
- O schema oficial do projeto é `topomemory`.
- O acesso oficial usa a rede interna `10.45.0.0/16`.

## Princípio de separação

O modelo separa observação bruta de entidade canônica. A mesma coisa observada várias vezes pode gerar múltiplas observações, mas converge para uma identidade canônica quando o sistema decide isso com base em evidências.

## Saúde operacional mínima

A Camada 2 mínima passa a persistir `route_snapshot` e `route_health_assessment` no mesmo schema `topomemory`.

- `route_snapshot` resume o run como rota
- `route_health_assessment` classifica a saúde mínima e a mudança estrutural
- a comparação entre runs equivalentes continua ancorada em `target_value` e `scenario`
- a rodada refinada separa `public_resolved_path_signature`, `private_resolved_path_signature` e `destination_stable_key`

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

Nesta rodada, a consolidação determinística cobre IP público, hostname/PTR forte e IP privado por contexto local. Os detalhes mínimos, as chaves de identidade e as limitações ficam em [LAYER1_BASELINE.md](/docs/LAYER1_BASELINE.md).

## Camada 1 semântica auxiliar

A frente semântica complementar registra perfil textual e embedding por `network_element` em tabela própria.

- `network_element_semantic`

Essa camada é auxiliar:

- consulta contexto com ranking vetorial
- não altera `network_element`
- não altera `identity_decision`
- não autoriza merge automático

Os detalhes operacionais ficam em [LAYER1_SEMANTIC_BASELINE.md](/docs/LAYER1_SEMANTIC_BASELINE.md).

## Auditoria operacional da Camada 1

A Camada 1 também passa a ter uma superfície SQL de auditoria para leitura operacional dos resultados do baseline, sem mexer na lógica de consolidação.

- a view `topomemory.v_layer1_identity_audit` organiza `observed_element`, `identity_decision` e `network_element`
- o objetivo é enxergar por `run_id` e `bundle_id` como cada observação foi tratada
- isso continua sendo leitura de auditoria; não é uma nova camada semântica

## Comparação entre runs da Camada 1

A Camada 1 também passa a ter uma superfície analítica para comparar dois runs já consolidados.

- a view `topomemory.v_layer1_run_elements` expõe a chave de comparação por identidade resolvida ou assinatura observacional
- a view `topomemory.v_layer1_run_diff_summary` resume cada run e sua sequência observada
- o objetivo é comparar estabilidade, diversidade e diferença de caminho sem alterar identidade mínima

## Observação

Este documento descreve apenas o modelo conceitual inicial. Não é o schema SQL definitivo e não substitui decisões de implementação futura.
