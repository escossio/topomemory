# Acesso ao banco

## Estado oficial

- database oficial do projeto: `topomemory`
- role oficial do projeto: `topomemory_app`
- schema oficial do projeto: `topomemory`
- host PostgreSQL: `10.45.0.3`
- rede autorizada: `10.45.0.0/16`
- autenticação: `scram-sha-256`

## Intenção operacional

O Topomemory deixou de depender de túnel SSH como caminho oficial para acessar o PostgreSQL.
O caminho oficial agora é conexão TCP direta ao host interno do banco pela rede `10.45.0.0/16`.

## Regras de acesso

- o acesso é restrito ao database `topomemory`
- o acesso é restrito ao role `topomemory_app`
- a autenticação usa senha com `scram-sha-256`
- não há liberação ampla para `0.0.0.0/0`
- não há uso de `trust`

## Configuração do servidor

O servidor PostgreSQL precisa escutar em:

- `localhost`
- `10.45.0.3`

Exemplo efetivo:

```conf
listen_addresses = 'localhost,10.45.0.3'
```

O `pg_hba.conf` precisa conter uma regra específica para o projeto:

```conf
host    topomemory    topomemory_app    10.45.0.0/16    scram-sha-256
```

## Bootstrap lógico

As etapas lógicas do banco do projeto são:

1. criar o role `topomemory_app`
2. criar o database `topomemory` com owner `topomemory_app`
3. criar o schema `topomemory` com owner `topomemory_app`
4. aplicar as migrations da Camada 0 e da Camada 1 nesse database
5. restaurar os dados do schema `topomemory` do estado anterior, se necessário

## Observação sobre histórico

O repositório ainda mantém a fase transitória que usava `livecopilot_app` e o banco `livecopilot` como histórico operacional.
Isso não é mais o caminho oficial do projeto.
