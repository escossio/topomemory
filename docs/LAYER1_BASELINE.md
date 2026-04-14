# Baseline mínimo da Camada 1

## O que já está pronto

A Camada 1 mínima já cobre três regras determinísticas de identidade canônica:

1. IP público por `canonical_ip`
2. hostname/PTR forte quando `canonical_ip` não existe
3. IP privado por assinatura determinística local baseada em vizinhança e posição

## Regra pública por IP

- usa `canonical_ip` público como chave primária
- hostname, ASN e org só reforçam a leitura de um IP já consolidado
- não faz merge entre IPs diferentes

## Regra pública por hostname/PTR

- só entra quando não existe `canonical_ip`
- usa normalização conservadora
- nome fraco ou conflito vira skip auditável
- hostname/PTR não substitui IP público existente

## Regra privada por assinatura local

- usa `observed_ip` privado
- incorpora `hop_index`
- incorpora `previous_neighbor_key`
- incorpora `next_neighbor_key`
- incorpora `service_context`
- não consolida IP privado por igualdade pura
- não usa ASN/org para decidir identidade

## Limites do baseline

- sem embeddings na identidade canônica
- sem `pgvector` como fonte da verdade da identidade
- sem merge semântico para decisão de identidade
- sem correlação frouxa por ASN/org
- sem grafo operacional
- sem heurísticas agressivas de hostname

## Frente semântica separada

A frente semântica auxiliar, quando usada, vive em tabela própria e não altera este baseline.
Ela pode enriquecer consulta e contexto, mas não participa da decisão determinística de identidade.

## Objetivo da camada

O baseline existe para manter a identidade canônica auditável, conservadora e idempotente antes da próxima frente semântica.

## Próxima frente operacional

A frente seguinte, sem abrir semântica, é a auditoria operacional da Camada 1 por `run_id` e `bundle_id`.

- ela lê o resultado do baseline sem alterar as regras de identidade
- ela expõe `decision_type`, `confidence`, `reasoning_summary` e o `network_element` resolvido
- ela ajuda a revisar `matched_existing_entity`, `new_entity_created` e `skipped_*` com clareza operacional

## Frente analítica complementar

Depois da auditoria, a próxima leitura útil é a comparação entre runs já consolidados.

- ela compara observações e identidades resolvidas
- ela não cria heurística nova
- ela ajuda a enxergar estabilidade e divergência entre coletas reais
