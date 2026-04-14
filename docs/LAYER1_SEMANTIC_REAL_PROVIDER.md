# Provider real da camada semântica

## Escolha

O provider real é `openai`.

## Configuração

Variáveis de ambiente usadas:

- `TOPOMEMORY_EMBEDDING_PROVIDER=openai`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL` opcional
- `TOPOMEMORY_EMBEDDING_MODEL` opcional, com padrão `text-embedding-3-small`

## Contrato

O provider real mantém:

- a tabela `topomemory.network_element_semantic`
- o texto de perfil semântico atual
- a dimensão vetorial de 128
- o benchmark fixo de 12 queries
- a identidade determinística da Camada 1

## Falha controlada

Se `OPENAI_API_KEY` não estiver configurada, a inicialização falha de forma explícita.
Não há fallback silencioso para outro motor.

## Reindexação

A reindexação continua idempotente por `element_id`.
Se o provider ou o modelo mudarem, os embeddings precisam ser recalculados para os elementos existentes.

