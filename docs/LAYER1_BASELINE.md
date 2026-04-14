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

- sem embeddings
- sem `pgvector` operacional na Camada 1
- sem merge semântico
- sem correlação frouxa por ASN/org
- sem grafo operacional
- sem heurísticas agressivas de hostname

## Objetivo da camada

O baseline existe para manter a identidade canônica auditável, conservadora e idempotente antes da próxima frente semântica.
