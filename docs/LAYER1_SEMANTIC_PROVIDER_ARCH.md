# Arquitetura de provider da camada semântica

## Objetivo

Desacoplar o cálculo de embedding da lógica de persistência e consulta semântica da Camada 1.

O objetivo desta refatoração é permitir troca futura de provider sem mexer no contrato da tabela semântica, sem alterar a identidade determinística e sem reescrever os scripts já existentes.

## Interface

O projeto usa uma interface conceitual simples:

- `model_name() -> str`
- `embed_text(text: str) -> list[float]`
- `embed_batch(texts: list[str]) -> list[list[float]]`

Essa interface é definida em `src/embedding_provider.py` e consumida por:

- `src/embed_network_elements.py`
- `src/search_network_elements_semantic.py`
- `src/semantic_support.py`

## Seleção por configuração

As variáveis de ambiente oficiais são:

- `TOPOMEMORY_EMBEDDING_PROVIDER`
- `TOPOMEMORY_EMBEDDING_MODEL`

Variáveis reservadas para provider externo futuro:

- `TOPOMEMORY_EXTERNAL_EMBEDDING_ENDPOINT`
- `TOPOMEMORY_EXTERNAL_EMBEDDING_API_KEY`
- `TOPOMEMORY_EXTERNAL_EMBEDDING_MODEL`

## Provider padrão

O provider padrão é `hash`.

Quando nenhuma variável é definida, o sistema mantém o comportamento atual com:

- provider: `hash`
- modelo: `topomemory-hash-embedding-v1`

## Provider real

O provider real desta árvore é `openai`.

Ele usa a API de embeddings da OpenAI por meio do SDK Python instalado no ambiente.

Variáveis esperadas:

- `OPENAI_API_KEY` obrigatório
- `OPENAI_BASE_URL` opcional
- `TOPOMEMORY_EMBEDDING_MODEL` opcional, com padrão `text-embedding-3-small`

Para manter o contrato da tabela semântica, a chamada solicita `dimensions=128`, preservando o tamanho do vetor já adotado na tabela `topomemory.network_element_semantic`.

Quando `OPENAI_API_KEY` estiver ausente, a inicialização falha de forma explícita e não tenta fallback silencioso.

## Provider hash

O `HashEmbeddingProvider` encapsula o comportamento atual.

Ele continua:

- determinístico
- reprodutível
- local
- livre de credenciais externas

Isso garante que a rodada atual não altera o resultado funcional já validado.

## Provider externo stub

O `ExternalEmbeddingProviderStub` existe apenas como contrato de expansão.

Ele não faz chamada real.
Ele falha de forma controlada se for selecionado sem a configuração mínima.
Ele também falha se for chamado com configuração completa, porque a integração real ainda não foi implementada nesta árvore.

Esse comportamento é intencional:

- deixa claro onde a integração futura entrará
- evita comportamento implícito
- impede a troca silenciosa de motor sem suporte real

## Compatibilidade com os scripts existentes

Os scripts já existentes continuam compatíveis porque:

- o provider padrão continua sendo hash
- a função `get_embedding_provider()` retorna o provider ativo
- o perfil semântico continua vindo de fatos auditáveis já presentes no banco
- a tabela `topomemory.network_element_semantic` continua sendo a mesma
- o benchmark semântico continua usando o mesmo dataset fixo

## Contrato operacional

Nesta fase, o provider semântico é apenas um detalhe de implementação.

A verdade operacional da Camada 1 continua sendo a identidade determinística.

O provider semântico:

- enriquece consulta
- não muda merge
- não muda auditoria
- não muda `identity_decision`
- não muda `network_element`
