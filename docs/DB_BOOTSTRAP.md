# Bootstrap do banco

## Pré-requisitos

- PostgreSQL já existente e acessível.
- Permissão para criar o schema lógico do projeto.
- A base tecnológica continua sendo `PostgreSQL + pgvector`.

## Ordem de aplicação

1. Aplicar a migration baseline: [sql/migrations/001_layer0_initial.up.sql](/sql/migrations/001_layer0_initial.up.sql)
2. Aplicar a seed mínima do collector: [sql/seeds/001_collector_vm_10.45.0.4.sql](/sql/seeds/001_collector_vm_10.45.0.4.sql)
3. Aplicar os GRANTs mínimos da Camada 0: [sql/001_layer0_minimum_grants.sql](/sql/001_layer0_minimum_grants.sql)

## Baseline

A migration versionada é a forma oficial de instalar a Camada 0 em um banco novo ou vazio.
Ela cria:

- `collector`
- `run`
- `run_artifact`
- `ingestion_bundle`

## Seed

A seed mínima registra o collector oficial inicial da Camada 0:

- `collector_id = vm-10.45.0.4`
- `collector_name = VM 10.45.0.4`
- `collector_type = controlled_vm`
- `location_hint = 10.45.0.4`
- `network_context` com a identificação operacional básica
- `is_active = true`

## GRANTs mínimos

O role de ingestão usa o mínimo necessário para persistir a coleta real:

- `USAGE` no schema `topomemory`
- `SELECT`, `INSERT`, `UPDATE`, `DELETE` nas tabelas `topomemory.collector`, `topomemory.run`, `topomemory.run_artifact` e `topomemory.ingestion_bundle`

O arquivo oficial é:

- [sql/001_layer0_minimum_grants.sql](/sql/001_layer0_minimum_grants.sql)

## Observação sobre escopo lógico

O bootstrap funciona tanto em:

- database dedicado `topomemory`
- schema dedicado `topomemory` em database compartilhado

A decisão de organização lógica não altera a migration nem a seed, apenas o ponto de instalação.

## Sobre o arquivo SQL histórico

O arquivo [sql/001_layer0_initial.sql](/sql/001_layer0_initial.sql) permanece como referência histórica da primeira versão do SQL inicial.
A migration versionada oficial é [sql/migrations/001_layer0_initial.up.sql](/sql/migrations/001_layer0_initial.up.sql).

## Limitações conhecidas

- Não há migrations down.
- Não há framework de migration.
- Não há seed adicional além do collector oficial inicial.
- Não há pipeline de coleta usando essas tabelas ainda.
- A conexão operacional inicial da VM usa túnel SSH reverso enquanto o PostgreSQL permanecer escutando apenas em `127.0.0.1`.
