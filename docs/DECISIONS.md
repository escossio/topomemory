# Decisões registradas

## Fechadas

- Nome do projeto: `topomemory`
- Diretório raiz oficial: `/srv/topomemory`
- Remote oficial: `git@github.com:escossio/topomemory.git`
- Banco principal: `PostgreSQL + pgvector`
- VM oficial de coleta inicial: `10.45.0.4`
- Prometheus é a camada temporal do sistema
- Zabbix é componente operacional, não o cérebro do sistema
- O grafo é projeção, não fonte da verdade
- A unidade operacional principal é a rota/entrega, não o hop isolado

## Bootstrap de arquivos e diretórios

- O repositório versiona a base documental, os diretórios de código e os placeholders mínimos necessários para manter a estrutura.
- Saídas geradas de execução real devem ficar fora do Git.
- `runs/` é reservado para execuções temporárias e evidências operacionais.
- `artifacts/` é reservado para saídas geradas, anexos e material derivado.

## Observações de arquitetura

- A base conceitual de dependências do serviço alimenta a Camada 2.
- A Camada 4 projeta o grafo operacional a partir da memória e da telemetria.
- A documentação do repositório é a primeira fonte oficial desta arquitetura inicial.

