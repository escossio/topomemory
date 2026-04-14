# Decisões registradas

## Fechadas

- Nome do projeto: `topomemory`
- Diretório raiz oficial: `/srv/topomemory`
- Remote oficial: `git@github.com:escossio/topomemory.git`
- Banco principal: `PostgreSQL`; `pgvector` é direção conceitual, ainda não operacional
- O projeto reutiliza a instância PostgreSQL já existente no ambiente
- Não haverá nova instância, serviço ou engine de banco nesta fase
- Database oficial do projeto: `topomemory`
- Role oficial do projeto: `topomemory_app`
- Schema oficial do projeto: `topomemory`
- Acesso oficial ao PostgreSQL: rede interna `10.45.0.0/16` com `scram-sha-256`
- O túnel SSH reverso deixou de ser o caminho oficial do projeto
- VM oficial de coleta inicial: `10.45.0.4`
- Prometheus é a camada temporal do sistema
- Zabbix é componente operacional, não o cérebro do sistema
- O grafo é projeção, não fonte da verdade
- A unidade operacional principal é a rota/entrega, não o hop isolado
- BGP público é uma frente futura de enriquecimento externo, não substitui a coleta local controlada
- a observação primária do sistema continua sendo a VM da Camada 0

## Decisão de persistência

- A decisão de banco é de organização lógica sobre a infraestrutura PostgreSQL já existente.
- A engine continua sendo PostgreSQL.
- O projeto deve ficar logicamente isolado, com ownership e fronteira documentados.
- A opção padrão é um database dedicado porque simplifica operação, permissões e manutenção.
- O schema dedicado continua sendo fallback válido quando o ambiente compartilhado exigir essa forma.
- O owner lógico do banco do projeto é `topomemory_app`.
- O acesso do projeto não depende mais de `livecopilot_app`.

## Bootstrap de arquivos e diretórios

- O repositório versiona a base documental, os diretórios de código e os placeholders mínimos necessários para manter a estrutura.
- Saídas geradas de execução real devem ficar fora do Git.
- `runs/` é reservado para execuções temporárias e evidências operacionais.
- `artifacts/` é reservado para saídas geradas, anexos e material derivado.

## Observações de arquitetura

- A base conceitual de dependências do serviço alimenta a Camada 2.
- A Camada 4 projeta o grafo operacional a partir da memória e da telemetria.
- A documentação do repositório é a primeira fonte oficial desta arquitetura inicial.
