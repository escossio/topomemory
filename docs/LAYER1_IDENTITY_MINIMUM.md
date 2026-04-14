# Identidade mínima da Camada 1

## Objetivo

Esta etapa inicia a identidade canônica da Camada 1 de forma conservadora e auditável.
O foco é consolidar observações públicas em `network_element` por regras determinísticas simples e registrar cada decisão em `identity_decision`.

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
- se a observação pública não tiver IP canônico, ela é deferida de forma explícita
- hostname, ASN e org podem reforçar a leitura de um IP já consolidado, mas não criam merge por si só

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

## Por que IP privado não entra ainda

Os IPs privados aparecem como parte da rota, mas esta rodada não quer misturar alcance interno com identidade canônica pública.
A decisão conservadora reduz risco de fusão errada e deixa a regra privada para uma etapa posterior, com mais contexto.

## Limitações conhecidas

- hostnames públicos sem IP canônico ficam deferidos nesta rodada
- não existe correlação semântica entre entidades
- não existe decisão probabilística
- não existe `pgvector`
- não existe merge por equivalência textual ampla
- não existe grafo operacional aberto a partir desta consolidação

## Próximos passos prováveis

- acrescentar uma segunda regra mínima para hostname canônico com controle explícito
- introduzir `role_hint_current` mais rico quando houver contexto suficiente
- incorporar IP privado em uma etapa separada, também por regra determinística
- depois disso, abrir correlação semântica e embeddings somente quando a base estiver estável
