# Regra mínima de hostname/PTR da Camada 1

## Objetivo

Reduzir `skipped_no_public_ip` em observações públicas sem IP canônico quando houver nome forte o bastante para uma identidade determinística, sem abrir embeddings, semântica pesada ou consolidação de IP privado.

## Princípio

- IP público continua sendo a chave primária quando existe
- hostname/PTR entra só como regra complementar para observações públicas sem IP canônico
- hostname/PTR não substitui o merge por IP público
- hostname/PTR não é usado para consolidar IP privado

## Campo canônico usado nesta regra

- preferencialmente `observed_hostname`
- fallback `observed_ptr`

## Normalização

- trim de espaços
- lowercase
- remoção de ponto final de FQDN
- rejeição de valores com espaço, barra ou barra invertida
- validação sintática simples de hostname DNS

## Quando o nome é forte

O nome é aceito quando:

- não está vazio após normalização
- contém pelo menos um ponto
- passa na validação sintática conservadora
- não é um nome obviamente genérico ou local
- `observed_hostname` e `observed_ptr` não entram em conflito direto

## Quando o nome é fraco

O nome é tratado como fraco quando:

- está vazio após normalização
- tem só um rótulo
- é `localhost`, `localdomain`, `local`, `unknown` ou equivalente óbvio
- não passa na validação sintática mínima

## Quando há conflito

Se `observed_hostname` e `observed_ptr` forem ambos fortes e diferentes:

- a observação é marcada como `skipped_hostname_conflict`
- nenhuma consolidação automática ocorre
- a trilha fica registrada em `identity_decision`

## Regra de consolidação

Para observações públicas sem IP canônico e com nome forte:

- cria `network_element` com `canonical_hostname`
- usa `matched_existing_entity` quando já existe uma entidade hostname-only igual
- usa `new_entity_created` quando a entidade ainda não existe
- mantém `canonical_ip = NULL`

## Proteção contra colisão

- hostname/PTR não é usado para anexar uma observação hostname-only a um elemento já consolidado por IP
- um elemento consolidado por IP não passa a ser identificado por hostname nesta rodada
- a regra evita merge indevido entre superfícies diferentes de identidade

## Tipos de decisão

- `matched_existing_entity`
- `new_entity_created`
- `skipped_private_scope`
- `skipped_no_public_ip`
- `skipped_hostname_weak`
- `skipped_hostname_conflict`

## Limites

- não há embeddings
- não há merge semântico
- não há consolidação automática de IP privado
- não há abertura do grafo operacional
- não há normalização agressiva de hostnames genéricos

## Validação esperada

Os runs reais devem mostrar:

- redução de `skipped_no_public_ip`
- criação de entidades hostname-only quando o nome for forte
- `skipped_hostname_weak` e `skipped_hostname_conflict` quando a regra não puder decidir com segurança
- reexecução sem duplicar `network_element`
