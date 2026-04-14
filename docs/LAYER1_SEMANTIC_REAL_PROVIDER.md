# Provider real da camada semântica

## Escolha

O provider real é `openai`.

## Configuração

Variáveis de ambiente usadas:

- `TOPOMEMORY_EMBEDDING_PROVIDER=openai`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL` opcional
- `TOPOMEMORY_EMBEDDING_MODEL` opcional, com padrão `text-embedding-3-small`

Fonte operacional da credencial nesta rodada:

- unit systemd: `livecopilot-semantic-api.service`
- `EnvironmentFile`: `/etc/livecopilot-semantic.env`

## Contrato

O provider real mantém:

- a tabela `topomemory.network_element_semantic`
- o texto de perfil semântico atual
- a dimensão vetorial de 128
- o benchmark fixo de 12 queries
- a identidade determinística da Camada 1

## Falha controlada

Se `OPENAI_API_KEY` não estiver configurada, a inicialização falha de forma explícita.
Nesta rodada a chave foi encontrada e carregada com sucesso, o provider foi ativado, 40 elementos foram reindexados e o benchmark fixo foi reexecutado.
Não há fallback silencioso para outro motor.

## Resultado observado

- hit_rate agregado: `0.6666666666666666`
- mean_first_hit_position: `1`
- `q12_private_hop_google`: `pass`
- leitura operacional: o provider real melhorou o caso combinado `q12`, mas piorou a estabilidade global em relação ao baseline hash

## Reindexação

A reindexação continua idempotente por `element_id`.
Se o provider ou o modelo mudarem, os embeddings precisam ser recalculados para os elementos existentes.
