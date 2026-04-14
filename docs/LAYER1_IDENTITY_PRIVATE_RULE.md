# Regra mínima de IP privado da Camada 1

## Objetivo

Consolidar observações privadas apenas quando houver contexto local suficiente no bundle/run para montar uma assinatura determinística conservadora.

## Princípio

- IP privado sozinho não identifica entidade
- IP privado não colide por igualdade pura
- a identidade privada depende da vizinhança e da posição local
- não há embeddings, scoring pesado ou merge semântico

## Assinatura privada

A chave privada usa, nesta ordem:

- `observed_ip` normalizado
- `hop_index`
- `previous_neighbor_key`
- `next_neighbor_key`
- `service_context`

## Como a vizinhança é localizada

- usa `observed_relation` do próprio bundle/run como fonte primária
- prefere relações `precedes` para derivar o vizinho anterior e o próximo
- se a relação não existir, cai para `element_index - 1` e `element_index + 1` como fallback documentado
- o vizinho usa `canonical_ip` pública quando existe, senão hostname/PTR forte, senão índice local do bundle

## Quando consolida

- `hop_index` existe
- `service_context` existe
- a assinatura privada pode ser montada sem conflito local
- a mesma assinatura já vista resolve para a mesma `network_element`

## Quando não consolida

- `skipped_private_insufficient_context` quando faltam `hop_index`, `service_context` ou vizinhos suficientes
- `skipped_private_conflict` quando a vizinhança local é ambígua ou conflita entre candidatos

## Resultado canônico

- `network_element.ip_scope = private`
- `canonical_ip = NULL`
- `canonical_hostname = NULL`
- `element_id` é derivado de um hash estável da assinatura privada
- `canonical_label` carrega uma etiqueta privada estável e auditável

## Limites

- não consolida IP privado por igualdade pura de IP
- não mistura contextos diferentes
- não usa ASN/org para decidir identidade privada
- não abre o grafo operacional
- esta regra é parte do baseline mínimo documentado em [LAYER1_BASELINE.md](/docs/LAYER1_BASELINE.md)

## Tipos de decisão

- `matched_existing_entity`
- `new_entity_created`
- `skipped_private_insufficient_context`
- `skipped_private_conflict`
- `skipped_hostname_weak`
- `skipped_hostname_conflict`
- `skipped_no_public_ip`
- `skipped_private_scope` como legado de compatibilidade

## Validação esperada

- redução de `skipped_private_scope`
- aumento de `matched_existing_entity` e `new_entity_created` para elementos privados
- `skipped_private_insufficient_context` e `skipped_private_conflict` só quando a assinatura não for segura
- reexecução idempotente por `observed_element_id` e por `element_id` estável
