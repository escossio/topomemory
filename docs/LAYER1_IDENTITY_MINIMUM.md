# Identidade mínima da Camada 1

## Objetivo

Esta etapa inicia a identidade canônica da Camada 1 de forma conservadora e auditável.
O foco é consolidar observações públicas em `network_element` por regras determinísticas simples e registrar cada decisão em `identity_decision`.
O baseline mínimo completo da Camada 1 está resumido em [LAYER1_BASELINE.md](/docs/LAYER1_BASELINE.md).

## Por que esta rodada é conservadora

- não usa embeddings
- não usa correlação semântica pesada
- não abre o grafo operacional
- não consolida IP privado automaticamente
- não faz merge por hostname sozinho
- não faz merge por ASN sozinho
- não faz merge por org sozinho
- não faz merge entre IPs diferentes

## Regra base desta rodada

- se a observação tiver IP privado ou reservado, a consolidação automática é adiada
- se a observação tiver IP público, a chave inicial de correspondência é `canonical_ip`
- se a observação pública não tiver IP canônico, hostname/PTR pode formar uma identidade canônica própria de forma determinística quando o nome passar pela normalização conservadora
- hostname, ASN e org podem reforçar a leitura de um IP já consolidado, mas não criam merge por si só
- hostname/PTR não substitui `canonical_ip` quando o IP público existir
- se a observação for privada, a identidade passa a depender de vizinhança e posição local no bundle/run, conforme a regra detalhada em [LAYER1_IDENTITY_PRIVATE_RULE.md](/docs/LAYER1_IDENTITY_PRIVATE_RULE.md)

## Escopo de `network_element`

`network_element` guarda a primeira identidade canônica mínima dos elementos públicos consolidados.

Campos principais:

- `element_id`
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
- `is_active`
- `created_at`
- `updated_at`

## Escopo de `identity_decision`

`identity_decision` registra o que foi decidido para cada `observed_element`.

Tipos de decisão nesta rodada:

- `matched_existing_entity`
- `new_entity_created`
- `skipped_private_scope`
- `skipped_no_public_ip`
- `skipped_hostname_weak`
- `skipped_hostname_conflict`
- `skipped_private_insufficient_context`
- `skipped_private_conflict`

## Por que IP privado não entra ainda

Os IPs privados aparecem como parte da rota e agora podem entrar apenas por regra determinística local, usando a vizinhança do bundle/run e a posição observada.
A decisão conservadora continua evitando merge por IP puro e deixa as situações sem contexto ou ambíguas para `skipped_private_insufficient_context` e `skipped_private_conflict`.
Essa regra privada faz parte do baseline mínimo, mas continua sem semântica, embeddings ou correlação frouxa.

## Limitações conhecidas

- não existe correlação semântica entre entidades
- não existe decisão probabilística
- não existe `pgvector`
- não existe merge por equivalência textual ampla
- não existe grafo operacional aberto a partir desta consolidação
- veja a regra complementar de hostname/PTR em [LAYER1_IDENTITY_HOSTNAME_RULE.md](/docs/LAYER1_IDENTITY_HOSTNAME_RULE.md)
- veja a regra complementar de IP privado em [LAYER1_IDENTITY_PRIVATE_RULE.md](/docs/LAYER1_IDENTITY_PRIVATE_RULE.md)
- veja o resumo único do baseline em [LAYER1_BASELINE.md](/docs/LAYER1_BASELINE.md)

## Próximos passos prováveis

- acrescentar uma segunda regra mínima para hostname canônico com controle explícito
- introduzir `role_hint_current` mais rico quando houver contexto suficiente
- incorporar IP privado em uma etapa separada, também por regra determinística
- depois disso, abrir correlação semântica e embeddings somente quando a base estiver estável
