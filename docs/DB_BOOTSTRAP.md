# Bootstrap do banco

## Pré-requisitos

- PostgreSQL já existente e acessível.
- Permissão para criar o schema lógico do projeto.
- A base tecnológica continua sendo `PostgreSQL + pgvector`.
- O database oficial do projeto é `topomemory`.
- O role oficial do projeto é `topomemory_app`.

## Ordem de aplicação

1. Criar o role e o database dedicados, conforme [Acesso ao banco](/docs/DATABASE_ACCESS.md)
2. Aplicar a migration baseline: [sql/migrations/001_layer0_initial.up.sql](/sql/migrations/001_layer0_initial.up.sql)
3. Aplicar a normalização mínima da Camada 1: [sql/migrations/002_layer1_observations.up.sql](/sql/migrations/002_layer1_observations.up.sql)
4. Aplicar a identidade canônica mínima da Camada 1: [sql/migrations/003_layer1_identity_minimal.up.sql](/sql/migrations/003_layer1_identity_minimal.up.sql)
5. Aplicar a regra conservadora de hostname/PTR da Camada 1: [sql/migrations/004_layer1_identity_hostname_rule.up.sql](/sql/migrations/004_layer1_identity_hostname_rule.up.sql)
6. Aplicar a regra determinística conservadora para IP privado: [sql/migrations/005_layer1_identity_private_rule.up.sql](/sql/migrations/005_layer1_identity_private_rule.up.sql)
7. Aplicar a view de auditoria operacional da Camada 1: [sql/migrations/006_layer1_audit_view.up.sql](/sql/migrations/006_layer1_audit_view.up.sql)
8. Aplicar a seed mínima do collector: [sql/seeds/001_collector_vm_10.45.0.4.sql](/sql/seeds/001_collector_vm_10.45.0.4.sql)

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

O acesso transitório da Camada 0 usou `livecopilot_app` como papel de ingestão.
O estado oficial do projeto usa `topomemory_app` no database `topomemory`, documentado em [Acesso ao banco](/docs/DATABASE_ACCESS.md).

- `USAGE` e `CREATE` no schema `topomemory`
- ownership do database `topomemory`
- ownership do schema `topomemory`
- permissões de criação/alteração sobre os objetos do próprio projeto

## Observação sobre escopo lógico

O bootstrap oficial agora prefere um database dedicado `topomemory`.
O schema dedicado em database compartilhado continua sendo fallback de infraestrutura, mas não é o caminho oficial desta rodada.

## Sobre o arquivo SQL histórico

O arquivo [sql/001_layer0_initial.sql](/sql/001_layer0_initial.sql) permanece como referência histórica da primeira versão do SQL inicial.
A migration versionada oficial é [sql/migrations/001_layer0_initial.up.sql](/sql/migrations/001_layer0_initial.up.sql).

## Limitações conhecidas

- Não há migrations down.
- Não há framework de migration.
- Não há seed adicional além do collector oficial inicial.
- Não há pipeline de coleta usando essas tabelas ainda.
- O acesso oficial ao PostgreSQL agora é direto pela rede interna `10.45.0.0/16`.
