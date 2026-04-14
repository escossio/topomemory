# topomemory

topomemory é o núcleo documental e arquitetural para organizar coleta controlada, memória canônica, saúde operacional e projeções do grafo de operação de rotas e entregas.

## Visão geral

O projeto separa observação, memória, saúde, tempo, projeção e ação em camadas explícitas. A intenção é manter um modelo disciplinado, auditável e fácil de evoluir sem misturar telemetria bruta com verdade canônica.

## Arquitetura em camadas

- Camada 0: Ambiente de Coleta Controlado
- Camada 1: Memória Topológica / Memória Canônica dos Elementos
- Base conceitual de dependências do serviço, alimentando a Camada 2
- Camada 2: Saúde Operacional da Rota
- Camada 3: Telemetria Temporal / Prometheus
- Camada 4: Projeção e Geração do Grafo Operacional
- Camada 5: Operação, Incidente e Ação

## Componentes principais

- VM oficial de coleta inicial: `10.45.0.4`
- Banco principal: `PostgreSQL + pgvector`
- Prometheus: camada temporal e base de séries observáveis
- Zabbix: componente operacional de monitoramento, não o cérebro do sistema

## Status atual

Fase de bootstrap arquitetural. A Camada 0 já tem schema conceitual persistível documentado; ainda não há implementação funcional da coleta nem schema SQL definitivo.

## Documentação

- [Arquitetura](/docs/ARCHITECTURE.md)
- [Camadas](/docs/LAYERS.md)
- [Decisões](/docs/DECISIONS.md)
- [VM 10.45.0.4](/docs/COLLECTOR_VM_10.45.0.4.md)
- [Modelo conceitual do banco](/docs/DATABASE_CONCEPT.md)
- [Schema conceitual da Camada 0](/docs/COLLECTION_SCHEMA_CONCEPT.md)
- [Contrato do run](/docs/RUN_CONTRACT.md)
- [Ingestion bundle](/docs/INGESTION_BUNDLE.md)
- [Formato do manifesto do run](/docs/RUN_MANIFEST_FORMAT.md)
- [Formato do ingestion bundle](/docs/INGESTION_BUNDLE_FORMAT.md)
