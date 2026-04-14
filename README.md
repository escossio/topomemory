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
- Banco principal: `PostgreSQL + pgvector`, com database dedicado `topomemory`
- Prometheus: camada temporal e base de séries observáveis
- Zabbix: componente operacional de monitoramento, não o cérebro do sistema

## Status atual

Fase de bootstrap arquitetural. A Camada 0 já tem coleta real mínima validada e agora opera com execução remota na VM `10.45.0.4` e persistência direta no PostgreSQL oficial `10.45.0.3:5432/topomemory` via `topomemory_app`, sem túnel SSH. A Camada 1 já normaliza `observed_elements` e `observed_relations` e agora inicia a identidade canônica mínima com `network_element` e `identity_decision`, ainda sem embeddings e sem consolidar IP privado automaticamente. A regra complementar por hostname/PTR reduz `skipped_no_public_ip` sem substituir a consolidação por IP público.

## Documentação

- [Arquitetura](/docs/ARCHITECTURE.md)
- [Camadas](/docs/LAYERS.md)
- [Decisões](/docs/DECISIONS.md)
- [VM 10.45.0.4](/docs/COLLECTOR_VM_10.45.0.4.md)
- [Modelo conceitual do banco](/docs/DATABASE_CONCEPT.md)
- [Acesso ao banco](/docs/DATABASE_ACCESS.md)
- [Schema conceitual da Camada 0](/docs/COLLECTION_SCHEMA_CONCEPT.md)
- [Notas do SQL inicial da Camada 0](/docs/LAYER0_SQL_NOTES.md)
- [Bootstrap do banco](/docs/DB_BOOTSTRAP.md)
- [Bootstrap operacional da Camada 0](/docs/LAYER0_OPERATIONAL_BOOTSTRAP.md)
- [Ingestão mínima da Camada 0](/docs/LAYER0_INGESTION.md)
- [Normalização mínima da Camada 1](/docs/LAYER1_MINIMAL_NORMALIZATION.md)
- [Contrato do run](/docs/RUN_CONTRACT.md)
- [Ingestion bundle](/docs/INGESTION_BUNDLE.md)
- [Formato do manifesto do run](/docs/RUN_MANIFEST_FORMAT.md)
- [Formato do ingestion bundle](/docs/INGESTION_BUNDLE_FORMAT.md)
