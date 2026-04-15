# Baseline semântico auxiliar da Camada 1

## Objetivo

Adicionar uma frente semântica separada da identidade canônica determinística da Camada 1.

A finalidade desta frente é enriquecer consulta e inspeção de `network_element`, sem alterar as decisões já consolidadas em `identity_decision`.

## Princípio principal

- a identidade determinística continua sendo a fonte da verdade
- o índice semântico é auxiliar
- embeddings não autorizam merge automático
- a busca semântica não reescreve `network_element`
- a busca semântica não reescreve `identity_decision`

## Tabela semântica

A base persistente fica em `topomemory.network_element_semantic`.

Campos principais:

- `semantic_id`
- `element_id`
- `semantic_profile_text`
- `semantic_profile_version`
- `embedding_model`
- `embedding_vector`
- `embedding_created_at`
- `created_at`
- `updated_at`

## Modelo adotado nesta primeira versão

- modelo de embedding: `topomemory-hash-embedding-v1`
- representação: vetor determinístico de 128 dimensões
- estratégia: hashing lexical reprodutível sobre o texto do perfil semântico

## Provider atual

- provider padrão: `hash`
- seleção por ambiente: `TOPOMEMORY_EMBEDDING_PROVIDER`
- modelo por ambiente: `TOPOMEMORY_EMBEDDING_MODEL`
- provider externo futuro: documentado em [LAYER1_SEMANTIC_PROVIDER_ARCH.md](/docs/LAYER1_SEMANTIC_PROVIDER_ARCH.md)
- provider real disponível: `openai`, documentado em [LAYER1_SEMANTIC_REAL_PROVIDER.md](/docs/LAYER1_SEMANTIC_REAL_PROVIDER.md)
- fonte operacional usada nesta rodada: `livecopilot-semantic-api.service` com `EnvironmentFile=/etc/livecopilot-semantic.env`
- variante vencedora atual do tuning: `hybrid_private_page8_focus`, configurada por `TOPOMEMORY_SEMANTIC_PROFILE_VARIANT`
- controle operacional atual para comparação focalizada: `hybrid`
- resultado do controle `hybrid`: `11/12`, com falha residual em `q10_private_node`
- resultado da vencedora focalizada: `12/12`, com reindexação de apenas `1` elemento privado

Este modelo foi escolhido porque:

- é determinístico
- é reproduzível
- não exige serviço externo
- cabe bem na primeira validação da infraestrutura
- permite consulta semântica auxiliar sem alterar a identidade canônica

## Chave de atualização

- a persistência é idempotente por `element_id`
- um único registro semântico representa o estado atual de cada `network_element`
- se o perfil textual mudar, o embedding correspondente é invalidado e recalculado
- se nada mudar, a execução é reprodutível e não precisa alterar o vetor persistido
- `embedding_model` agora grava o nome real do modelo ativo, evitando reembed completo quando nenhum perfil mudou

## Perfil semântico

O `semantic_profile_text` é construído de forma determinística a partir de fatos já existentes no banco:

- `canonical_label`
- `element_kind`
- `ip_scope`
- `canonical_ip`
- `canonical_hostname`
- `canonical_asn`
- `canonical_org`
- `confidence_current`
- `role_hint_current`
- `first_seen_at`
- `last_seen_at`
- contagens auditáveis de decisões
- tipos de origem observados
- escopos observados
- contextos de serviço observados

## Consulta semântica

A consulta é feita por CLI com um texto livre e retorna os `network_element` mais próximos no espaço vetorial.

Saída mínima:

- `element_id`
- `canonical_ip`
- `canonical_hostname`
- `canonical_org`
- `role_hint_current`
- `score`
- `distance`
- trecho do `semantic_profile_text`

## Limites desta frente

- não cria identidade nova
- não funde entidades
- não altera `network_element`
- não altera `identity_decision`
- não substitui auditoria
- não substitui diff entre runs
- não abre grafo
- não usa a busca semântica como verdade operacional

## Leitura operacional

Esta frente existe para recuperar contexto com rapidez e para preparar a evolução futura.
Ela é útil para consulta e enriquecimento, mas continua subordinada ao baseline determinístico da Camada 1.

## Avaliação

A avaliação do baseline semântico fica documentada em [LAYER1_SEMANTIC_EVAL.md](/docs/LAYER1_SEMANTIC_EVAL.md).
O dataset de queries vive em [schemas/semantic_eval_queries.json](/schemas/semantic_eval_queries.json), e os artefatos de execução ficam em [artifacts/semantic-eval/README.md](/artifacts/semantic-eval/README.md).

## Troca de motor

A tentativa de trocar o motor de embedding está documentada em [LAYER1_SEMANTIC_MOTOR_CHANGE.md](/docs/LAYER1_SEMANTIC_MOTOR_CHANGE.md).
O provider real `openai` já foi ativado com sucesso no ambiente Livecopilot, e a camada semântica passou por tuning focalizado sem mexer na identidade determinística.
